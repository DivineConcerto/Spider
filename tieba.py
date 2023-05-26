import json
import scrapy
import os


class TiebaSpider(scrapy.Spider):
    name = 'tieba'
    start_urls = ['https://tieba.baidu.com/f?kw=吧名']

    custom_settings = {
        'ITEM_PIPELINES': {'tieba.TiebaPipeline': 1},
    }

    def parse(self, response):
        # 选取所有的帖子链接
        for href in response.css('a.j_th_tit::attr(href)').extract():
            url = response.urljoin(href)
            yield scrapy.Request(url, callback=self.parse_post)

        # 追踪下一页
        next_page = response.css('a.next::attr(href)').get()
        if next_page is not None:
            next_page = response.urljoin(next_page)
            yield scrapy.Request(next_page, callback=self.parse)

    def parse_post(self, response):
        # 提取帖子标题和内容
        yield {
            'title': response.css('h1.core_title_txt::text').get(),
            'post': response.css('div.d_post_content.j_d_post_content::text').get(),
        }

        # 提取所有回复
        for reply in response.css('div.l_post'):
            yield {
                'reply': reply.css('div.d_post_content.j_d_post_content::text').get(),
            }


class TiebaPipeline:

    def process_item(self, item, spider):
        with open('./data.txt','a') as file:
            if 'title' in item:
                text = item['title'] + '\n' + item['post'] + '\n'
            else:
                text = item['reply']
            if text.strip():
                text = text.replace(' ', '')
                file.write(text)
        return item

    def close_spider(self,spider):
        with open('data.txt', 'r') as source_file:
            block_size = 50
            text = source_file.read().replace('\n', '')
        blocks = [text[i:i + block_size] for i in range(0, len(text), block_size)]
        with open('source.txt', 'w') as src_file:
            for block in blocks:
                src_file.write(block + '\n')
        # 删除源文件
        os.remove('source.txt')
        # 将临时文件重命名为源文件
        os.rename('temp.txt', 'source.txt')
