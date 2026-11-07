"""Serve the repository with byte ranges required for MP4 event seeking."""
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
import os
import re


class Handler(SimpleHTTPRequestHandler):
    def send_head(self):
        self.byte_range=None
        path=self.translate_path(self.path)
        requested=self.headers.get('Range')
        if not requested or not os.path.isfile(path):return super().send_head()
        # An If-Range condition needs an exact validator match. Returning a
        # complete 200 response is safe when this server cannot establish it.
        if self.headers.get('If-Range'):return super().send_head()
        match=re.fullmatch(r'bytes=(\d*)-(\d*)',requested.strip())
        if not match:return super().send_head()
        try:stream=open(path,'rb')
        except OSError:self.send_error(404,'File not found');return None
        info=os.fstat(stream.fileno());size=info.st_size;left,right=match.groups()
        if left:
            start=int(left);end=min(size-1,int(right)) if right else size-1
        elif right:
            start=max(0,size-int(right));end=size-1
        else:
            stream.close();self.send_error(400,'Empty byte range');return None
        if start>end or start>=size:
            stream.close();self.send_response(416);self.send_header('Content-Range',f'bytes */{size}');self.send_header('Content-Length','0');self.end_headers();return None
        self.send_response(206);self.send_header('Content-Type',self.guess_type(path))
        self.send_header('Content-Range',f'bytes {start}-{end}/{size}');self.send_header('Content-Length',str(end-start+1))
        self.send_header('Last-Modified',self.date_time_string(info.st_mtime));self.end_headers()
        self.byte_range=(start,end);stream.seek(start);return stream

    def end_headers(self):
        self.send_header('Accept-Ranges','bytes');super().end_headers()

    def copyfile(self,source,outputfile):
        if self.byte_range is None:return super().copyfile(source,outputfile)
        remaining=self.byte_range[1]-self.byte_range[0]+1
        try:
            while remaining:
                block=source.read(min(65536,remaining))
                if not block:break
                outputfile.write(block);remaining-=len(block)
        except (BrokenPipeError,ConnectionResetError):pass


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=8768);parser.add_argument('--bind',default='127.0.0.1');args=parser.parse_args()
    root=Path(__file__).resolve().parents[2]
    server=ThreadingHTTPServer((args.bind,args.port),partial(Handler,directory=str(root)))
    print(f'http://{args.bind}:{args.port}/simulation/cooling_v1/sample.html',flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()
