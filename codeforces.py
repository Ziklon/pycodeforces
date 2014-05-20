from HTMLParser import HTMLParser
from urllib2 import urlopen
import os, re, sys
import thread
import time
import datetime as dt
import signal
from subprocess import Popen, PIPE, STDOUT

url='http://codeforces.com/contest/432'

class ProblemHTMLParser(HTMLParser):
    class Node:
        def __init__(self, tag, attrs):
            self.tag = tag
            self.attrs = attrs
            self.children = []
            self.data = ''
    def __init__(self):
        self.reset()
        self.stack = []
        self.sample_input_nodes = []
        self.recording = False
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        sample_input_div = tag == 'div' and attrs.get('class', '').find('sample') != -1
        if self.recording or sample_input_div:
            self.recording = True
            node = ProblemHTMLParser.Node(tag, attrs)
            if self.stack:
                if tag == 'br':
                    self.stack[-1].data += '\n'
                else:
                    self.stack[-1].children.append(node)
            self.stack.append(node)
    def handle_endtag(self, tag):
        if self.recording:
            node = self.stack.pop()
            if not self.stack:
                self.sample_input_nodes.append(node)
                self.recording = False
    def handle_data(self, data):
        if self.recording:
            self.stack[-1].data += data
    def walkNodes(self, node, output_pre_datas):
        if node.tag == 'pre':
            output_pre_datas.append(node.data)
        else:
            for child in node.children:
                self.walkNodes(child, output_pre_datas)
    def getExamples(self):
        if not self.sample_input_nodes:
            return []

        assert len(self.sample_input_nodes) == 1
        pre_datas = []
        self.walkNodes(self.sample_input_nodes[0], pre_datas)

        assert len(pre_datas) % 2 == 0

        examples = []
        for i in range(0, len(pre_datas), 2):
            examples.append((pre_datas[i], pre_datas[i+1]))
        return examples


all_created=True
fileTemplate = open("template.cpp","r")
textTemplate=""
while True:
    tmp = fileTemplate.readline()
    if len(tmp)==0:
        break
    textTemplate=textTemplate+tmp

for i in range(0,10):
    curUlr=url+'/problem/'+chr(i+ord('A'))
    problem_html = urlopen(curUlr).read()
    problem_html = problem_html.replace('<p</p>', '<p></p>')
    problem_html = problem_html.replace('<ul</ul>', '<ul></ul>')
    problem_html = problem_html.replace('<div class="sample-test"<', '<div class="sample-test">')
    parser = ProblemHTMLParser()
    try:
        parser.feed(problem_html)
        sample = parser.getExamples()
        
        if len(sample) == 0:
            break
        nameSource=chr(i+ord('A'))+".cpp"
        if os.path.isfile(nameSource)==False:
            sourceFile=open(nameSource,"w")
            sourceFile.write(textTemplate)
            sourceFile.close()
        curFile = open("created/task"+chr(i+ord('A')),"w")        
        curFile.write("%d\n"%len(sample))
        #print "NUMCASES %s %d\n" %( chr(i+ord('A')), len(sample))
        for j in range(len(sample)):
            curFile.write("INPUT******%d\n%s" %(j+1,sample[j][0]))
            curFile.write("OUPUT******%d\n%s" %(j+1,sample[j][1]))
            curFile.write("SEPARATOR******\n")
        curFile.close()
    except:
        print problem_html
        all_created=False
        raise
if all_created:
    print 'All problems created succefull'
else:
    print 'Some problems ocurred'

def compile(source):

    os.remove('a.exe')

    res=os.system("g++ "+source)

    print '\n******************* Compiling %s ********************\n'%(source)
    if res==0:
        task='created/task'+source[0]
        curFile =open(task,"r")
        cases=int(curFile.readline())
        all_test_passed=True
        for i in range(cases):
            cad=curFile.readline()
            textInput=""
            textOutput=""
            while True:
                tmp=curFile.readline()
                if str.startswith(tmp,"OUPUT******")==True:
                    break
                textInput=textInput+tmp
            while True:
                tmp=curFile.readline()
                if str.startswith(tmp,"SEPARATOR******")==True:
                    break
                textOutput=textOutput+tmp
            
            inputFile= open("input","w")
            textInput=textInput.strip()
            textOutput=textOutput.strip()            
            inputFile.write(textInput)
            inputFile.close()
            print '******************************************'
            print "Case Number %d"%(i+1)
            cmd = 'a.exe < input'
            pipe = Popen(cmd, shell=True, stdout=PIPE)
            
            for i in range(40):
                if pipe.poll() is not None:
                    break
                time.sleep(.1)    
            retcode = pipe.poll()
            if retcode is not None:
                outputCode = pipe.stdout.read()
                outputCode=outputCode.strip()          
                if outputCode != textOutput:
                    all_test_passed=False
                    print '%s\nExpected\n%s\nReceived\n%s\n'%(textInput,textOutput, outputCode)
                else:
                    print 'Test Passed\n'
            else:
                message=Popen("taskkill /F /T /PID %i"%pipe.pid )
                #os.kill(pipe.pid, signal.signal(sig, action))
                all_test_passed =False
                print "TIME LIMIT EXCIDED\n"
                 
        if all_test_passed:
            print "All test case passed :)"
        else:
            print "Some wrong in your algorithm :("
        
    else:
        print 'Compilation Error'

def checkChange():
    now=dt.datetime.now()
    ago=now-dt.timedelta(seconds=.5)
    for root,dirs,files in os.walk('.'): 
        for fname in files:
            if str.endswith(fname,".cpp"):
                path=os.path.join(root,fname)
                st=os.stat(path)
                mtime=dt.datetime.fromtimestamp(st.st_mtime)            
                if mtime>=ago:
                    compile(fname)
                    
while True:
    checkChange()
    time.sleep(.5)
