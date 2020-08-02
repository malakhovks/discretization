#!/usr/bin/env bash
# test_data.pdf contains the document you want to post
# -p means to POST it
# -H adds an Auth header (could be Basic or Token)
# -T sets the Content-Type
# -c is concurrent clients
# -c is number of concurrent requests, example: `-n 7 -c 5` will do 7 requests in total: first 5 then 2
# -n is the number of requests to run in the test

ab -v 2 -n 10 -c 10 -T 'multipart/form-data; boundary=1234567890' -p post_service4.txt http://178.128.245.158:45101/api/confor/service/3/4?find=find