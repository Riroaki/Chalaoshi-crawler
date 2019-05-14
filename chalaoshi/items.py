import scrapy


# Records all information of a teacher
class TeacherItem(scrapy.Item):
    name = scrapy.Field()
    index = scrapy.Field()
    # Rates of a teacher
    rate_avg = scrapy.Field()
    rate_count = scrapy.Field()
    rate_call_roll = scrapy.Field()
    # College and department
    college = scrapy.Field()
    department = scrapy.Field()
    # List of course items and comment items
    course_list = scrapy.Field()  # a course is a dict {name, gpa_avg, gpa_count}
    comment_count = scrapy.Field()


# Records all comments for a teacher
class CommentListItem(scrapy.Item):
    name = scrapy.Field()
    comment_count = scrapy.Field()
    comment_list = scrapy.Field()  # a comment is a dict {text, vote, time}
