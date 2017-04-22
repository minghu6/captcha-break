#!/usr/bin/env python
# coding:utf-8
from __future__ import absolute_import
from __future__ import print_function

import os
import sys
from subprocess import Popen, PIPE
try:
    import cpickle as pickle
except ImportError:
    import pickle

import tensorflow as tf
import numpy as np
import cv2

from common import load_label_map, IMAGE_SIZE
from load_model_nn import load_model_nn
import __init__ # run init
from spliter import Spliter

image_size = IMAGE_SIZE

def find_model_ckpt(model_ckpt_dir=os.curdir):
    """Find Max Step model.ckpt"""
    from distutils.version import LooseVersion
    model_ckpt_tuple_list = []
    for fn in os.listdir(model_ckpt_dir):
        if fn.startswith('weibo.cn-model.ckpt'):
            version = fn.split('weibo.cn-model.ckpt')[1]
            model_ckpt_tuple_list.append((version, fn))

    if len(model_ckpt_tuple_list) == 0:
        raise FileNotFoundError('file like weibo.cn-model.ckpt')
    model_ckpt_list = list(sorted(model_ckpt_tuple_list,
                                  key=lambda item:LooseVersion(item[0])))
    fn = model_ckpt_list[-1][1]
    fn = os.path.splitext(fn)[0] #remove ext
    path = os.path.join(model_ckpt_dir, fn)

    return path

def recognise_char_p():
    label_map = load_label_map()
    model = load_model_nn()

    x = model['x']
    keep_prob = model['keep_prob']
    saver=model['saver']
    prediction = model['prediction']
    graph = model['graph']
    model_ckpt_path = find_model_ckpt('.checkpoint')
    #print('load check-point %s'%model_ckpt_path, file=sys.stderr)
    with tf.Session(graph=graph) as session:
        tf.global_variables_initializer().run()
        saver.restore(session, model_ckpt_path)

        while True:
            sys.stdout.flush()
            captcha_path = input().strip()
            if captcha_path == '$exit': # for close session
                break
            im = np.reshape(cv2.imread(captcha_path, cv2.IMREAD_GRAYSCALE), IMAGE_SIZE)
            label = prediction.eval(feed_dict={x: [im], keep_prob: 1.0}, session=session)[0]
            sys.stdout.write(label_map[label])
            sys.stdout.write('\n')


def recognize_p():
    """ 
    captcha_path
    $exit to exit
    """

    label_map = load_label_map()
    model = load_model_nn()

    x = model['x']
    keep_prob = model['keep_prob']
    saver=model['saver']
    prediction = model['prediction']
    graph = model['graph']
    model_ckpt_path = find_model_ckpt('.checkpoint')
    #print('load check-point %s'%model_ckpt_path, file=sys.stderr)
    with tf.Session(graph=graph) as session:
        tf.global_variables_initializer().run()
        saver.restore(session, model_ckpt_path)

        while True:
            sys.stdout.flush()
            captcha_path = input().strip()
            if captcha_path == '$exit': # for close session
                break

            spliter = Spliter(os.curdir)

            try:
                letters = spliter.split_letters(captcha_path)
                formatted_letters = map(spliter.format_splited_image,letters)
                formatted_letters = [letter.reshape(image_size) for letter in formatted_letters]
            except Exception as ex:
                sys.stdout.write('\n')
                continue

            result = []
            for letter in formatted_letters:
                label = prediction.eval(feed_dict={x: [letter], keep_prob: 1.0}, session=session)[0]
                result.append(label_map[label])
                sys.stdout.write(label_map[label])

            sys.stdout.write('\n')



# start a recognise daemon process
# for interactive in IPython
# p.send('test.gif')
# p.recv()
# p.close()

def send(self, msg):
    """Interactive Tools
    self: subprocess.Popen
    p.send('abc.png')
    send(p, 'abc.png')
    
    _read_time: in case of block forever for no SIGALARM on Windows 555
    """
    if sys.version_info.major == 2:
        Str = unicode
    else:
        Str = str

    if isinstance(msg, Str):
        msg = msg.encode('utf8')

    try:
        self.stdin.write(msg+b'\n')
        self.stdin.flush()
    except OSError:
        raise IOError('this process halted')

    _read_time = getattr(self, '_read_time', 0)
    if _read_time > 100:
        raise BufferError('Warning: may no have enough space in buffer')

    setattr(self, '_read_time', _read_time+1)


def recv(self, readall=False):
    """return str/unicode"""

    _read_time = getattr(self, '_read_time', 0)
    if _read_time == 0:
        raise IOError('you should send a value before recv')

    if readall:
        msg_list=[]
        for i in range(_read_time):
            msg_list.append(self.stdout.readline().strip().decode())
        msg = ''.join(msg_list)
        _read_time = 0
    else:
        msg=self.stdout.readline().strip().decode()
        _read_time -= 1


    setattr(self, '_read_time', _read_time)
    return msg

def close(self):
    self.stdin.write(b'$exit\n')

def enhance_popen(p):
    from types import MethodType

    p.send=MethodType(send, p)
    p.recv=MethodType(recv, p)
    p.close=MethodType(close, p)

    return p

def start_recognise_char_daemon():
    p = Popen([sys.executable, __file__, 'recognise_char'],
              bufsize=102400,
              stdin=PIPE, stdout=PIPE, stderr=PIPE)
    p.stdin.encoding = 'utf8' # so we get `str` instead of `bytes` in p
    p=enhance_popen(p)
    return p

def start_recognize_daemon():

    p = Popen([sys.executable, __file__],
              bufsize=102400,
              stdin=PIPE, stdout=PIPE, stderr=PIPE)
    p.stdin.encoding = 'utf8' # so we get `str` instead of `bytes` in p
    p=enhance_popen(p)
    return p

def cli():
    if len(sys.argv)==1:
        recognize_p()
    elif len(sys.argv) ==2:
        if sys.argv[1] == 'recognise_char':
            recognise_char_p()
        elif sys.argv[1] == 'recognise':
            recognize_p()

if __name__ == '__main__':
    cli()







