import os, sys, base64, pickle, json

url_file = 'download_urls'
tmp_file = url_file + '.tmp'
urls = pickle.loads(base64.b64decode(open(url_file, 'r').read()))
js = json.dumps(urls, indent='    ')
open(tmp_file, 'w').write(js)

os.system('nano ' + tmp_file)

urls = json.load(open(tmp_file, 'r'))
b64p = base64.b64encode(pickle.dumps(urls))
open(url_file, 'wb').write(b64p)
os.remove(tmp_file)
