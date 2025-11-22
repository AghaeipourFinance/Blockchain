from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA256

mykey = RSA.generate(3072)

############################### Public KEY
pk = mykey.public_key().export_key()
print(pk)
print('*'*100)
# with open("mypublickey.pem", "wb") as f:
#     data = mykey.public_key().export_key()

############################### Private KEY
pwd = b'secret'

sk = mykey.export_key(passphrase=pwd , pkcs=8 , protection='PBKDF2WithHMAC-SHA512AndAES256-CBC' 
                            , prot_params={'iteration_count':131072})
print(sk)
print('*'*100)
# with open("myprivatekey.pem",'wb') as f:
#     data = mykey.export_key(passphrase=pwd , pkcs=8 , protection='PBKDF2WithHMAC-SHA512AndAES256-CBC' 
#                             , prot_params={'iteration_count':131072})
#     f.write(data)

# with open("myprivatekey.pem",'rb'):
#     data = f.read()
#     mykey = RSA.import_key(data , pwd)
#     print(mykey)

############################### Signature
signer = PKCS1_v1_5.new(mykey)

message = b"hello world"
h = SHA256.new(message)

signature = signer.sign(h)
print(signature)


