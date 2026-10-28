"""Verify byte-accurate responses used by real browser media seeking."""
import http.client
from functools import partial
from http.server import ThreadingHTTPServer
from pathlib import Path
import tempfile
import threading
import unittest
from serve import Handler


class QuietHandler(Handler):
    def log_message(self,*args):pass


class RangeTest(unittest.TestCase):
    def test_media_ranges(self):
        with tempfile.TemporaryDirectory() as root:
            payload=bytes(range(256))*20;Path(root,'clip.mp4').write_bytes(payload)
            server=ThreadingHTTPServer(('127.0.0.1',0),partial(QuietHandler,directory=root))
            thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            try:
                for value,start,end in [('bytes=2-17',2,17),('bytes=5000-',5000,5119),('bytes=-12',5108,5119),('bytes=5000-99999',5000,5119)]:
                    connection=http.client.HTTPConnection(*server.server_address);connection.request('GET','/clip.mp4',headers={'Range':value});response=connection.getresponse()
                    self.assertEqual(response.status,206);self.assertEqual(response.read(),payload[start:end+1]);self.assertEqual(response.getheader('Content-Range'),f'bytes {start}-{end}/{len(payload)}');connection.close()
                connection=http.client.HTTPConnection(*server.server_address);connection.request('GET','/clip.mp4',headers={'Range':'bytes=99999-'});response=connection.getresponse();self.assertEqual(response.status,416);self.assertEqual(response.read(),b'');connection.close()
                connection=http.client.HTTPConnection(*server.server_address);connection.request('HEAD','/clip.mp4',headers={'Range':'bytes=2-17'});response=connection.getresponse();self.assertEqual(response.status,206);self.assertEqual(response.getheader('Content-Length'),'16');self.assertEqual(response.read(),b'');connection.close()
                connection=http.client.HTTPConnection(*server.server_address);connection.request('GET','/clip.mp4',headers={'Range':'bytes=2-17','If-Range':'unknown'});response=connection.getresponse();self.assertEqual(response.status,200);self.assertEqual(response.read(),payload);connection.close()
            finally:server.shutdown();server.server_close();thread.join()


if __name__=='__main__':unittest.main()
