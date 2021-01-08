from scrapy import Spider
from scrapy.http import Request, FormRequest

class EplanningSpider(Spider):
    name = 'eplanning'
    allowed_domains = ['eplanning.ie']
    start_urls = ['http://eplanning.ie/']

    def parse(self, response):
        urls = response.xpath('//a/@href').extract() 
        for url in urls:
            if '#' == url: #some urls in the list contains '#' entries and we don't need them
                pass
            else:
                yield Request(url, callback = self.parse_application) 

    def parse_application(self, response):
        app_url = response.xpath('//*[@class="glyphicon glyphicon-inbox btn-lg"]/following-sibling::a/@href').extract_first() #data from the first instance following the defined class
        yield Request(response.urljoin(app_url), callback = self.parse_form) #we manage to extract part url so in order to crawl the url we perform urljoin to get to the entire url 

    def parse_form(self, response):
        yield FormRequest.from_response(response,
                                        formdata = {'RdoTimeLimit': '42'}, #setting the parameter that we changed from default
                                        dont_filter = True, 
                                        formxpath = '(//form)[2]', #second form contains the data we need, so we define the xpath that navigates to the second form
                                        callback = self.parse_pages) 

    def parse_pages(self, response):
        application_urls = response.xpath('//td/a/@href').extract() #fetching the table data by means of every single row
        for url in application_urls: #iterating over rows
            url = response.urljoin(url) #scraped urls are incomplete, using urljoin to put them in complete form
            yield Request(url, callback = self.parse_items) #redirecting the crawler to the parse items method for scraping further data

        next_page_url = response.xpath('//*[@rel="next"]/@href').extract_first() #moving the crawler to the next page in the list of pages 
        absolute_next_page_url = response.urljoin(next_page_url) #using urljoin to complete the next page url from where data needs to be scraped
        yield Request(absolute_next_page_url, callback = self.parse_pages) #redirecting the crawler to parse pages method for parsing tables from the next page

    def parse_items(self,response):
        agent_btn = response.xpath('//*[@value="Agents"]/@style').extract_first() #path to crawl agent data for every application
        if "display: inline;  visibility: visible;" in agent_btn: #not all applications have agents, but when inspected the agents value exists for all 
            name = response.xpath('//tr[th="Name :"]/td/text()').extract_first() #applications but not visible for some. We'll only scrape the visible ones 
                                                                                 #using the if else statement
            address_first = response.xpath('//tr[th="Address :"]/td/text()').extract()
            address_second = response.xpath('//tr[th="Address :"]/following-sibling::tr/td/text()').extract()[0:2]
            
            address = address_first + address_second

            phone = response.xpath('//tr[th="Phone :"]/td/text()').extract_first()

            fax = response.xpath('//tr[th="Fax :"]/td/text()').extract_first()

            email = response.xpath('//tr[th="e-mail :"]/td/a/text()').extract_first()

            url = response.url

            yield {'name':name,                  #Agent data scraped
                   'address':address,
                   'phone':phone,
                   'fax':fax,
                   'email':email,
                   'url':url}

        else:
            self.logger.info('Agent button not found on page, passing invalid url.')  #Message to be displayed if agents not visible   
