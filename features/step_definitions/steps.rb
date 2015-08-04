require 'net/http'
require 'json'
require 'rspec'


def elastic_search(data)
    uri = URI('http://localhost:9200')
    http = Net::HTTP::new(uri.host, uri.port)
    request = Net::HTTP::Post.new('/index/names/_search?size=1000')
    request['Content-Type'] = 'application/json'
    request.body = data
    response = http.request(request)
    response
end

def delete_item(id)
    uri = URI('http://localhost:9200')
    http = Net::HTTP::new(uri.host, uri.port)
    request = Net::HTTP::Delete.new("/index/names/#{id}")
    request['Content-Type'] = 'application/json'
    response = http.request(request)
    response
end


Before do |scenario|
    if scenario.name == "New Registers are Converted & Added to Names-Search"
        response = elastic_search('{"query": {"match": {"title_number": "ST44730"}}}')
        data = JSON.parse(response.body)
        data['hits']['hits'].each do |hit|
            id = hit['_id']
            delete_item(id)
            puts "deleted #{id}"
        end
    end
end

Given(/^new data is posted to the queue$/) do
    `vagrant ssh -c "python3 /vagrant/apps/name-index-generator/fire_at_queue.py /vagrant/apps/name-index-generator/reg2.json"`
end

When(/^the system runs$/) do
end

Then(/^the reformatted data is stored in ElasticSearch$/) do
    sleep(1)
    response = elastic_search('{"query": {"match": {"title_number": "ST44730"}}}')
    expect(response.code).to eq "200"
    data = JSON.parse(response.body)
    expect(data['hits']['total']).to eq 1
    expect(data['hits']['hits'][0]['_source']['title_number']).to eq "ST44730"
end





# localhost:9200/index/names/_search?size=1000

# {"query": {"match": {"title_number": "ST44730"}}}
#{
  #"took": 5,
  #"timed_out": false,
  #"_shards": {
    #"total": 5,
    #"successful": 5,
    #"failed": 0
  #},
  #"hits": {
    #"total": 1,
    #"max_score": 0.30685282,
    #"hits": [
      #{
        #"_index": "index",
        #"_type": "names",
        #"_id": "AU74DerKrTlzYDohC01U",
        #"_score": 0.30685282,
        #"_source": {
          #"title_number": "ST44730",
          #"office": "Kaden Office",
          #"registered_proprietor": {
            #"forenames": [
              #"Raina",
              #"Laurie"
            #],
            #"full_name": "Raina Laurie Zieme",
            #"surname": "Zieme"
          #},
          #"name_type": "Private",
          #"sub_register": "Proprietorship"
        #}
      #}
    #]
  #}
#}
