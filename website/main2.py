from flask import Flask, render_template, url_for, request, session, redirect,jsonify,Response
from threading import Thread
import time
from ftplib import FTP
from client.client_chat import Client
from client.client_stream import ClientStream
from client.mic_client import ClientAudio
from client.helper_classes_sel import receiver
import socket
import smtplib
import binascii
import pyaudio
import base64
import io
import random

global serverport
global servername

host_ip = '192.168.43.58'


serverport= 587
servername = 'smtp.gmail.com'

N_KEY = "name"
app = Flask(__name__)
app.secret_key = "123456"
messages = []
clients_connected = {}
ftp = FTP('ftp.drivehq.com')
ftp.login(user='waficLawand', passwd = 'June201999!@#$%')

def disconnect():    
        client = ''
        client.disconnect()



@app.route("/login",methods=["POST","GET"])
def login():
    ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
    if request.method == "POST":
        print(request.form)
        session[N_KEY] = request.form["inputName"]
        client = Client(session[N_KEY])
        clients_connected[ip] = client
        return redirect(url_for("home"))
    return render_template("login.html",**{"session":"session"})
    

@app.route("/logout", methods=["POST", "GET"])
def logout():
    ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
    clients_connected[ip].disconnect()
    session.pop(N_KEY,None)
    return redirect(url_for("login"))

@app.route("/",methods=["POST","GET"])
@app.route("/home",methods=["POST","GET"])
def home():
    ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)

    if ip not in clients_connected:
        return redirect(url_for("login"))
        
    else:
        
        
        return render_template("index.html",**{"login":True,"session":"session"})

def gen():
    """Video streaming generator function."""
    client = ClientStream()
    while True:
        frame = client.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

def genHeader(sampleRate, bitsPerSample, channels):
        datasize = 2000*10**6
        o = bytes("RIFF",'ascii')                                               # (4byte) Marks file as RIFF
        o += (datasize + 36).to_bytes(4,'little')                               # (4byte) File size in bytes excluding this and RIFF marker
        o += bytes("WAVE",'ascii')                                              # (4byte) File type
        o += bytes("fmt ",'ascii')                                              # (4byte) Format Chunk Marker
        o += (16).to_bytes(4,'little')                                          # (4byte) Length of above format data
        o += (1).to_bytes(2,'little')                                           # (2byte) Format type (1 - PCM)
        o += (channels).to_bytes(2,'little')                                    # (2byte)
        o += (sampleRate).to_bytes(4,'little')                                  # (4byte)
        o += (sampleRate * channels * bitsPerSample // 8).to_bytes(4,'little')  # (4byte)
        o += (channels * bitsPerSample // 8).to_bytes(2,'little')               # (2byte)
        o += (bitsPerSample).to_bytes(2,'little')                               # (2byte)
        o += bytes("data",'ascii')                                              # (4byte) Data Chunk Marker
        o += (datasize).to_bytes(4,'little')
        return o                

def gen_audio():

    CHANNELS = 1
    RATE = 44100
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT, channels=CHANNELS,
                        rate=RATE, input=True,input_device_index=1,
                        frames_per_buffer=CHUNK)

    client = ClientAudio()
    wav_header = genHeader(RATE, 16, CHANNELS)
    
    first_run = True
    while True:
        if first_run:
                
            data = wav_header + client.get_audio()
            first_run = False
        else:
            data = client.get_audio()
        yield(data)
   


@app.route("/video_feed")
def video_feed():
    return Response(gen(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')
@app.route("/send_message",methods=["GET"])
def send_message():
    ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
    message = request.args.get("val")
    print("clicked")
    print(message)
    clients_connected[ip].send_message(message)
    return "none"

@app.route("/get_messages",methods=["GET"])    
def get_messages():
    return jsonify({"messages":messages}) 

def update_messages():
    """
    updates the local list of messages
    :return: None
    """
    global messages
    run = True
    while run:
        time.sleep(0.1)  # update every 1/10 of a second
        if len(clients_connected) == 0: continue
        new_messages = clients_connected[host_ip].get_messages()  # get any new messages from client
        messages.extend(new_messages)  # add to local list of messages

        for msg in new_messages:  # display new messages
            if(msg == "{quit}"):
                run = False
                break
            

@app.route("/files")
def files():
    dir_list = []
    files = []
    ftp.dir(dir_list.append)

    for line in dir_list:
       files.append(line[29:].strip().split(' ')[4])
    return render_template("files.html",files = files)

@app.route("/download", methods = ["GET","POST"])
def download():
        
        
        print("downloading")
        filename = request.form['filedownload']
        print(filename)
        
        if('.' not in filename and filename != 'Back'):
            ftp.cwd('/'+filename)
            #ftp_downloader.cwd('/'+filename)
        elif(filename == 'Back'):
            ftp.cwd('../')
            #ftp_downloader.cwd('/'+filename)
            
        else:
            localfile = open(filename, 'wb')
            ftp.retrbinary('RETR ' + filename, localfile.write, 1024)
            localfile.close()
            in_file = open(filename, "rb")
            data = in_file.read()
            in_file.close()
            
            #file = ftp_downloader.download(filename)
        
            return Response(
                data,
                mimetype="text/plain",
                headers={"Content-disposition":
                         "attachment; filename="+filename+""})
            
            
        
        return redirect(url_for("files"))
@app.route("/upload", methods = ["GET","POST"])
def upload():
        
        print("downloading")
        path = request.form['filename']
        data = request.form['data']
        print(path)
        filename = path.rsplit('\\', 1)[-1]
        data = data.rsplit(',', 1)[-1].encode("ascii")
        print(data)
        decoded = base64.decodebytes(data)
        bio = io.BytesIO(decoded)
        
         
        ftp.storbinary('STOR '+filename,bio)
        return redirect(url_for("files"))

            
            
        
        return redirect(url_for("files"))
@app.route("/sendemail")
def myform():
    return render_template("mail.html")
@app.route("/sendemail", methods = ["GET","POST"])
def sendemail():
    
    clientemail = ''
    clientpassword = ''
    destinationemail = ''
    emailsubject = ''
    emailbody = ''
    
    clientemail = request.form["email"]
    clientpassword = request.form["password"]
    destinationemail = request.form["destemail"]
    emailsubject = request.form["subject"]
    emailbody = request.form["body"]
    try:
        conn = smtplib.SMTP(servername, serverport)
        conn.ehlo()
        conn.starttls()
        conn.login(clientemail, clientpassword)
        conn.sendmail(clientemail, destinationemail, 'Subject:' + emailsubject + '\n\n' + emailbody)
        conn.quit()
        print('Success')
    except smtplib.SMTPServerDisconnected:
            print('Server disconnected unexpectedly')
            return 'Server disconnected unexpectedly'
    except smtplib.SMTPSenderRefused:
            print('Sender address invalid')
            return 'Sender address invalid'
    except smtplib.SMTPRecipientsRefused:
            print('All recipient addresses have been refused')
            return 'All recipient addresses have been refused'
    except smtplib.SMTPDataError:
            print('SMTP Server does not accept the message data')
            return 'SMTP Server does not accept the message data'
    except smtplib.SMTPConnectError:
            print('Could not establish a connection with the server')
            return 'Could not establish a connection with the server'
    except smtplib.SMTPHeloError:
            print('Server refuses the HELO message')
            return 'Server refuses the HELO message'
    except smtplib.SMTPAuthenticationError:
            print('Authentication Error, Incorrect username or password')
            return 'Authentication Error, Incorrect username or password. Try allowing unsecure logins to your account'
    except:
            print('Unknown Error')
            return 'Unknown Error'

    return redirect("home")



@app.route('/podcast',methods = ["GET","POST"])
def podcast():
    return render_template('podcast.html')

            
@app.route('/audio',methods = ["GET","POST"])
def audio():
    print(request.remote_addr)
    if request.remote_addr != host_ip:
        return Response(gen_audio(),mimetype='audio/wav')
    return redirect("home")
    


@app.route('/ham',methods = ["GET","POST"])
def ham():
    return render_template('hammingCode.html')

@app.route('/simulateHam',methods = ["GET","POST"])
def simulateHam():
    hamContent = []
    data = request.form['hamText']
    hamContent.append('Input String: '+data+'\n')
    print(data)
    data_binary = bin(int(binascii.hexlify(data.encode('ascii')),16))
    hamContent.append('Binary Data: '+data_binary+'\n')
    print(data_binary)
    extracted_bits = random.randint(0, len(data_binary)-4)
    print(extracted_bits)
    ham_data = data_binary[extracted_bits]+data_binary[extracted_bits+1]+data_binary[extracted_bits+2]+data_binary[extracted_bits+3]
    hamContent.append('Extracted Bits for Testing: '+ham_data+'\n')
    print(ham_data)
    
    G = ['1101', '1011', '1000', '0111', '0100', '0010', '0001']
    H = ['1010101', '0110011', '0001111']
    Ht = ['100', '010', '110', '001', '101', '011', '111']
    R = ['0010000', '0000100', '0000010', '0000001']
    p = ham_data
    
    print('Input bit string: ' + p)
    x = ''.join([str(bin(int(i, 2) & int(p, 2)).count('1') % 2) for i in G])
    hamContent.append('Encoded bit string to send: '+x+'\n')
    print('Encoded bit string to send: ' + x)
    # add 1 bit error
    e = random.randint(0, 7)
    print('Which bit got error during transmission (0: no error): ' + str(e))
    hamContent.append('Index of error bit: '+str(e)+'\n')
    if e > 0:
     x = list(x)
     x[e - 1] = str(1 - int(x[e - 1]))
     x = ''.join(x)
    hamContent.append('Encoded bit string that got error during tranmission: '+x+'\n')
    print ('Encoded bit string that got error during tranmission: ' + x)
    z = ''.join([str(bin(int(j, 2) & int(x, 2)).count('1') % 2) for j in H])
    if int(z, 2) > 0:
     e = int(Ht[int(z, 2) - 1], 2)
    else:
     e = 0
    hamContent.append('Index of error bit: '+str(e)+'\n')
    print('Which bit found to have error (0: no error): ' + str(e))
    
    p = ''.join([str(bin(int(k, 2) & int(x, 2)).count('1') % 2) for k in R])
    
    print(p)
    s = int(data_binary[0:extracted_bits]+p[0:4]+data_binary[extracted_bits+4:len(data_binary)],2)

    hamContent.append('Input String with errors: '+str(binascii.unhexlify('%x' % s))+'\n')
    if e > 0:
     x = list(x)
     x[e - 1] = str(1 - int(x[e - 1]))
     x = ''.join(x)
    p = ''.join([str(bin(int(k, 2) & int(x, 2)).count('1') % 2) for k in R])
    hamContent.append('Corrected output bit string: '+p+'\n')
    hamContent.append('Corrected String: '+data+'\n')
    
    print(hamContent)
    return render_template('hammingCode.html',hamContent = hamContent)


@app.route('/sel',methods = ["GET","POST"])
def sel():
    return render_template('selectiveRepeat.html')

@app.route('/simulateSel',methods = ["GET","POST"])
def simulateSel():
        
    packetsLost = []
    packetsLost = receiver.main()
    return render_template('selectiveRepeat.html',packetsLost = packetsLost)   
    
if __name__ == '__main__':
    Thread(target=update_messages).start()
    app.run(host=host_ip,port = 5000, threaded=True,debug=False)
    
    
    
    


    