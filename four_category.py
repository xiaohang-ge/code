import tensorflow as tf
import cv2
import numpy as np
import os
import random
import sys
from sklearn.model_selection import train_test_split
from tensorflow.python.framework import graph_util

import matplotlib.pyplot as plt
 
my_faces_path = './daisy'
other_faces_path = './dandelion'
my_faces_path1 = './roses'
other_faces_path1 = './sunflowers'
size = 64
 
imgs = []
labs = []
 
def getPaddingSize(img):
    h, w, _ = img.shape
    top, bottom, left, right = (0,0,0,0)
    longest = max(h, w)
 
    if w < longest:
        tmp = longest - w
        # //表示整除符号
        left = tmp // 2
        right = tmp - left
    elif h < longest:
        tmp = longest - h
        top = tmp // 2
        bottom = tmp - top
    else:
        pass
    return top, bottom, left, right
 
def readData(path , h=size, w=size):
    for filename in os.listdir(path):
        if filename.endswith('.jpg'):
            filename = path + '/' + filename
 
            img = cv2.imread(filename)
 
            top,bottom,left,right = getPaddingSize(img)
            # 将图片放大， 扩充图片边缘部分
            img = cv2.copyMakeBorder(img, top, bottom, left, right, cv2.BORDER_CONSTANT, value=[0,0,0])
            img = cv2.resize(img, (h, w))
 
            imgs.append(img)
            labs.append(path)
 
readData(my_faces_path)
readData(other_faces_path)
readData(my_faces_path1)
readData(other_faces_path1)
lab1s=[]
lab2s=[]
lab3s=[]
lab4s=[]

# 将图片数据与标签转换成数组
imgs = np.array(imgs)
lab1s = np.array([[1,0,0,0] for lab in labs if lab == my_faces_path])
#print(lab1s)
lab2s = np.array([[0,1,0,0] for lab in labs if lab == other_faces_path])
#print(lab2s)
lab3s = np.array([[0,0,1,0] for lab in labs if lab == my_faces_path1])
#print(lab3s)
lab4s = np.array([[0,0,0,1] for lab in labs if lab == other_faces_path1])
#print(lab4s)
#lab1s = np.array([0 if lab == my_faces_path else 1 for lab in labs])
#lab2s = np.array([2 if lab == my_faces_path else 3 for lab in labs])
#print(lab1s)
#labs=lab1s+lab2s+lab3s+lab4s
labs=np.concatenate((lab1s,lab2s,lab3s,lab4s))
print(labs)
# 随机划分测试集与训练集
train_x,test_x,train_y,test_y = train_test_split(imgs, labs, test_size=0.05, random_state=random.randint(0,100))
# 参数：图片数据的总数，图片的高、宽、通道
train_x = train_x.reshape(train_x.shape[0], size, size, 3)
test_x = test_x.reshape(test_x.shape[0], size, size, 3)
# 将数据转换成小于1的数
train_x = train_x.astype('float32')/255.0
test_x = test_x.astype('float32')/255.0
 
print('train size:%s, test size:%s' % (len(train_x), len(test_x)))
# 图片块，每次取100张图片
batch_size = 5
num_batch = len(train_x) // batch_size
 
x = tf.placeholder(tf.float32, [None, size, size, 3])
y_ = tf.placeholder(tf.float32, [None, 4])
print(y_)
 
keep_prob_5 = tf.placeholder(tf.float32)
keep_prob_75 = tf.placeholder(tf.float32)
 
def weightVariable(shape):
    init = tf.random_normal(shape, stddev=0.01)
    return tf.Variable(init)
 
def biasVariable(shape):
    init = tf.random_normal(shape)
    return tf.Variable(init)
 
def conv2d(x, W):
    return tf.nn.conv2d(x, W, strides=[1,1,1,1], padding='SAME')
 
def maxPool(x):
    return tf.nn.max_pool(x, ksize=[1,2,2,1], strides=[1,2,2,1], padding='SAME')
 
def dropout(x, keep):
    return tf.nn.dropout(x, keep)
 
def cnnLayer():
    # 第一层
    W1 = weightVariable([3,3,3,32]) # 卷积核大小(3,3)， 输入通道(3)， 输出通道(32)
    b1 = biasVariable([32])
    # 卷积
    conv1 = tf.nn.relu(conv2d(x, W1) + b1)
    # 池化
    pool1 = maxPool(conv1)
    # 减少过拟合，随机让某些权重不更新
    drop1 = dropout(pool1, keep_prob_5)
 
    # 第二层
    W2 = weightVariable([3,3,32,64])
    b2 = biasVariable([64])
    conv2 = tf.nn.relu(conv2d(drop1, W2) + b2)
    pool2 = maxPool(conv2)
    drop2 = dropout(pool2, keep_prob_5)
 
    # 第三层
    W3 = weightVariable([3,3,64,64])
    b3 = biasVariable([64])
    conv3 = tf.nn.relu(conv2d(drop2, W3) + b3)
    pool3 = maxPool(conv3)
    drop3 = dropout(pool3, keep_prob_5)

    # 第四层
    W4 = weightVariable([3,3,64,128])
    b4 = biasVariable([128])
    conv4 = tf.nn.relu(conv2d(drop3, W4) + b4)
    pool4 = maxPool(conv4)
    drop4 = dropout(pool4, keep_prob_5)

    # 第五层
    W5 = weightVariable([5,5,128,128])
    b5 = biasVariable([128])
    conv5 = tf.nn.relu(conv2d(drop4, W5) + b5)
    pool5 = maxPool(conv5)
    drop5 = dropout(pool5, keep_prob_5)
 
    # 全连接层
    Wf = weightVariable([2*2*128, 512])
    bf = biasVariable([512])
    drop3_flat = tf.reshape(drop5, [-1, 2*2*128])
    dense = tf.nn.relu(tf.matmul(drop3_flat, Wf) + bf)
    dropf = dropout(dense, keep_prob_75)
 
    # 输出层
    Wout = weightVariable([512,4])
    bout = weightVariable([4])
    #out = tf.matmul(dropf, Wout) + bout
    out = tf.add(tf.matmul(dropf, Wout), bout)
    return out
 
def cnnTrain():
    out = cnnLayer()
 
    cross_entropy = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(logits=out, labels=y_))
 
    train_step = tf.train.AdamOptimizer(0.1).minimize(cross_entropy)
    # 比较标签是否相等，再求的所有数的平均值，tf.cast(强制转换类型)
    accuracy = tf.reduce_mean(tf.cast(tf.equal(tf.argmax(out, 1), tf.argmax(y_, 1)), tf.float32))
    # 将loss与accuracy保存以供tensorboard使用
    tf.summary.scalar('loss', cross_entropy)
    tf.summary.scalar('accuracy', accuracy)
    merged_summary_op = tf.summary.merge_all()
    # 数据保存器的初始化
    saver = tf.train.Saver()
    
    with tf.Session() as sess:
        fig_loss = np.zeros([10000])
        fig_accuracy = np.zeros([10000])
        sess.run(tf.global_variables_initializer())
 
        summary_writer = tf.summary.FileWriter('./tmp', graph=tf.get_default_graph())
        graph_def = tf.get_default_graph().as_graph_def()
        constant_graph = graph_util.convert_variables_to_constants(sess, sess.graph_def, ['add'])
        #global_step = tf.Variable(0)
        #learning_rate = tf.train.exponential_decay(learning_rate=0.8, global_step=global_step, decay_rate=0.99, decay_steps=550, staircase=True) #指数衰减学习率
        for n in range(10):
             # 每次取128(batch_size)张图片
            for i in range(num_batch):
                batch_x = train_x[i*batch_size : (i+1)*batch_size]
                batch_x = np.reshape(batch_x, (-1, size, size, 3))
                batch_y = train_y[i*batch_size : (i+1)*batch_size]
                #global_step = tf.Variable(0)
                #learning_rate = tf.train.exponential_decay(learning_rate=0.8, global_step=global_step, decay_rate=0.99, decay_steps=550, staircase=True) #指数衰减学习率
                #learing_rate_decay = tf.train.exponential_decay(learning_rate=0.5, global_step=n*num_batch+i, decay_steps=10, decay_rate=0.9, staircase=False)
                #optimizer = tf.train.GradientDescentOptimizer(learning_rate=learning_rate).minimize(cross_entropy, global_step=global_step)
                # 开始训练数据，同时训练三个变量，返回三个数据
                _,loss,summary = sess.run([train_step, cross_entropy, merged_summary_op],
                                           feed_dict={x:batch_x,y_:batch_y, keep_prob_5:0.5,keep_prob_75:0.75})
                summary_writer.add_summary(summary, n*num_batch+i)
                # 打印损失
                fig_loss[n*num_batch+i]=loss
                print(n*num_batch+i, loss)

 
                if (n*num_batch+i) % 10 == 0:
                    # 获取测试数据的准确率
                    acc = accuracy.eval({x:test_x, y_:test_y, keep_prob_5:1.0, keep_prob_75:1.0})
                    #print(n*num_batch+i, acc)
                    fig_accuracy[n*num_batch+i]=acc
                    with tf.gfile.FastGFile('model.pb', mode='wb') as f:
                            f.write(constant_graph.SerializeToString())
                    #fig_loss[n*num_batch+i] = sess.run(cross_entropy, {x:batch_x,y_:batch_y, keep_prob_5:0.5,keep_prob_75:0.75})
                    #fig_accuracy[n*num_batch+i] = sess.run(accuracy, feed_dict={x:test_x, y_:test_y, keep_prob_5:1.0, keep_prob_75:1.0})
                    # 准确率大于0.98时保存并退出
                    #if acc > 0.98 and n > 2:
                    #if acc > 0.90:
                        #with tf.gfile.FastGFile('model.pb', mode='wb') as f:
                            #f.write(constant_graph.SerializeToString())
                        #saver.save(sess, './train_faces.model', global_step=n*num_batch+i)
                        #sys.exit(0)
        fig, ax1 = plt.subplots()
        ax2 = ax1.twinx()
        lns1 = ax1.plot(np.arange(1000), fig_loss, label="Loss")
        lns2 = ax2.plot(np.arange(1000), fig_accuracy, 'r', label="Accuracy")
        ax1.set_xlabel('iteration')
        ax1.set_ylabel('training loss')
        ax2.set_ylabel('training accuracy')
        lns = lns1 + lns2
        labels = ["Loss", "Accuracy"]
        plt.legend(lns, labels, loc=7)
        plt.show()
        print('accuracy less 0.98, exited!')
 
cnnTrain()
