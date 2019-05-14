import scrapy
import math
import json
import re
import os
from chalaoshi.items import TeacherItem, CommentListItem
from chalaoshi.settings import SAVE_FILE, MAX_INDEX

COUNT_PER_PAGE = 10


class ChalaoshiSpider(scrapy.Spider):
    name = 'chalaoshi'
    allowed_domains = ['chalaoshi.cn']
    start_urls = ['https://chalaoshi.cn/']

    # Record saved teachers and comments
    saved_data = {}

    # Teacher info url
    teacher_url = 'https://chalaoshi.cn/teacher/{index}'
    # Comment info url
    comment_url = 'https://chalaoshi.cn/teacher/{index}/comment_list?page={page}&order_by=rate'

    # Teacher info patterns
    teacher_name_pat = re.compile('<h3>(.*)</h3>')
    rate_pat = re.compile('<h2>(.*)</h2>')
    details_pat = re.compile('<p>(.*)</p>')
    comment_count_pat = re.compile('<p class="two">([\d]*)')

    # Comment patterns
    comment_text_pat = re.compile('<p>\n\s{16}([\s\S]*?)\n\s{12}</p>')
    comment_vote_pat = re.compile('<p class="\d*-count">\s*(-?\d*)\s*</p>')
    comment_time_pat = re.compile('<p class="comment-footer">发布于\s*(\d{4}\.\d{2}\.\d{2})\s*<a href="#" onclick')

    # Handle invalid status
    handle_httpstatus_list = [400, 401, 402, 403, 404, 500, 501, 502]

    # Find next teacher not fetched
    def find_next(self, index):
        while index in self.saved_data:
            index += 1
        return index

    # Calculate priority according to the index
    @staticmethod
    def calc_prior(index):
        return (MAX_INDEX - index) * 100

    # Entry of spider
    def start_requests(self):
        # Start from index last loaded if saved_file exists
        if os.path.exists(SAVE_FILE):
            with open(SAVE_FILE, 'r') as f:
                json_dict = json.load(f)
                # Remember json dict use str as keys, needs transformation back to int
                self.saved_data = {int(k): v for k, v in json_dict.items()}
        else:
            self.saved_data = {}
        # Start to find index from 1
        index = self.find_next(1)
        if index <= MAX_INDEX:
            yield scrapy.Request(self.teacher_url.format(index=index), callback=self.parse,
                                 priority=self.calc_prior(index), meta={'index': index})
        else:
            print('All teachers within {} has been collected:)'.format(MAX_INDEX))

    # Parse teacher information
    def parse(self, response):
        index = response.meta['index']
        code = response.status
        # Check status code
        if code in self.handle_httpstatus_list:
            self.saved_data[index] = {'name': 'Not applicable', 'comment_count': 0}
            # Invalid teacher index
            if 400 <= code < 500:
                print('Invalid teacher index {}, or network failed.'.format(index))
                index = self.find_next(index + 1)
                if index <= MAX_INDEX:
                    yield scrapy.Request(self.teacher_url.format(index=index), callback=self.parse,
                                         priority=self.calc_prior(index), meta={'index': index})
                else:
                    print('All teachers within {} has been collected:)'.format(MAX_INDEX))
            # Server not available
            elif code >= 500:
                print('Internal server error: chalaoshi.cn is not available now.')
            return
        content = response.text
        item = TeacherItem()
        try:
            # Basic information, use splice to remove `<...>`s
            item['index'] = index
            item['name'] = self.teacher_name_pat.search(content).group()[4:-5]
            item['rate_avg'] = self.rate_pat.search(content).group()[4:-5]
            # Details: strings between `<p>` and `</p>`
            details = self.details_pat.findall(content)
            item['college'] = details[0]
            item['department'] = details[1]
            # Parse other details
            course_index = 4
            if details[2] == '尚未收到足够的评分':
                item['rate_call_roll'] = 'N/A'
                item['rate_count'] = 0
                course_index = 3
            else:
                item['rate_call_roll'] = details[2][:details[2].find('%') + 1]
                item['rate_count'] = int(details[3][:details[3].find('人参与评分')])
            # Parse courses
            item['course_list'] = []
            while course_index < len(details):
                course = {'name': details[course_index], 'gpa_avg': details[course_index + 1].split('/')[0],
                          'gpa_count': details[course_index + 1].split('/')[1]}
                item['course_list'].append(course)
                course_index += 2
            # Parse comment counts
            count = self.comment_count_pat.search(content)
            if count is None:
                item['comment_count'] = 0
            else:
                item['comment_count'] = int(count.group()[15:])
            # Give item to pipeline
            yield item
            # Get comments
            if item['comment_count'] > 0:
                comments = CommentListItem()
                comments['name'] = item['name']
                comments['comment_count'] = item['comment_count']
                comments['comment_list'] = []
                # Page index starts from 0
                page_total = int(math.ceil(item['comment_count'] / COUNT_PER_PAGE)) - 1
                yield scrapy.Request(self.comment_url.format(index=index, page=0), callback=self.parse_comments,
                                     meta={'page_index': 0, 'item': comments, 'page_total': page_total,
                                           'index': index}, priority=self.calc_prior(index))
            else:
                self.saved_data[index] = {'name': item['name'], 'comment_count': item['comment_count']}
            print('Fetched teacher {} named {}.'.format(index, item['name']))
        # Something went wrong for my regex expression or teacher information
        except AttributeError as e:
            print('Error parsing teacher with index: {}: {}'.format(index, e))
        finally:
            # Fetch next teacher recursively
            # Start from index + 1 since current index is not done yet:
            # as comments are not parsed, the current index will not be in the saved dict
            index = self.find_next(index + 1)
            if index <= MAX_INDEX:
                yield scrapy.Request(self.teacher_url.format(index=index), callback=self.parse,
                                     priority=self.calc_prior(index), meta={'index': index})
            else:
                print('All teachers within {} has been collected:)'.format(MAX_INDEX))

    # Parse one page each containing at most 10 comments
    def parse_comments(self, response):
        # Recover param
        item = response.meta['item']
        page_index = response.meta['page_index']
        page_total = response.meta['page_total']
        index = response.meta['index']
        # Parse contents
        content = response.text.replace('&nbsp;', ' ')
        texts = self.comment_text_pat.findall(content)
        votes = self.comment_vote_pat.findall(content)
        times = self.comment_time_pat.findall(content)
        # This means something went wrong for my regex expression
        # Or the content of comments
        try:
            for i in range(len(texts)):
                comment = {'text': texts[i], 'vote': int(votes[i]), 'time': times[i]}
                item['comment_list'].append(comment)
        except AttributeError as e:
            print('Error parsing comments with teacher index {} at page {}: {}'.format(index, item.page_index, e))
            print(content)
        finally:
            page_index += 1
            if page_index <= page_total:
                yield scrapy.Request(self.comment_url.format(index=index, page=page_index),
                                     callback=self.parse_comments,
                                     meta={'page_index': page_index, 'item': item, 'page_total': page_total,
                                           'index': index}, priority=self.calc_prior(index))
            if item['comment_count'] == len(item['comment_list']):
                print('Fetched {} comments from teacher {}.'.format(item['comment_count'], item['name']))
                self.saved_data[index] = {'name': item['name'], 'comment_count': item['comment_count']}
                yield item

    @staticmethod
    def close(spider, reason):
        # Overwrite saved data records
        with open(SAVE_FILE, 'w') as f:
            # json will transform int keys into string keys
            json.dump(spider.saved_data, f, ensure_ascii=False, separators=(',', ': '), indent=4)
