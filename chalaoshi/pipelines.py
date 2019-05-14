from chalaoshi.items import CommentListItem, TeacherItem
from chalaoshi.settings import DOWNLOAD_FOLDER
import os
import json


class ChalaoshiPipeline(object):
    @classmethod
    def process_item(cls, item, _):
        name = item['name']
        filename = ''
        if isinstance(item, TeacherItem):
            filename = '{}/{}.txt'.format(DOWNLOAD_FOLDER, name)
        elif isinstance(item, CommentListItem):
            # Sort by votes (from large to small votes), as the comments may not be in order
            item['comment_list'] = sorted(item['comment_list'], key=lambda comment: -comment['vote'])
            filename = '{}/{}-评论.txt'.format(DOWNLOAD_FOLDER, name)
        # Check if file already exists
        if not os.path.exists(filename):
            with open(filename, 'w') as f:
                json.dump(dict(item), f, ensure_ascii=False, separators=(',', ': '), indent=4)
        return item
