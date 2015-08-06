import re
import os 
dn_re_slash = re.compile(r'(?:/)(.+?)(?:=)([^/]+)')
dn_re_comma = re.compile(r'(?:,|^)(.+?)(?:=)([^,]+)')

def parse_dn(dn):
    ans = dict(dn_re_slash.findall(dn))
    if len(ans) <= 1:
        ans = dict(dn_re_comma.findall(dn))
    return ans

#Note, two values for 'O' so cmp will randomly fail depending on dict order.
server_dn = '/C=US/ST=California/L=LaJolla/O=General Atomics/O=c21f969b5f03d33d43e04f8f136e7682/OU=GAT/CN=MPO-UI-SERVER/emailAddress=abla@fusion.gat.com'
server_dn = 'emailAddress=abla@fusion.gat.com,CN=MPO-UI-SERVER,OU=GAT,O=c21f969b5f03d33d43e04f8f136e7682,O=General Atomics,L=LaJolla,ST=California,C=US'
server_dict = parse_dn(server_dn)


#JCW Notes
# When used in the context of the Demo server since SSL Cert auth is off, we only have access to DEMO_AUTH
# and rely on it being set.
def get_user_dn(request):
#        import getpass
        try:
                ans = request.environ['HTTPS_DN']
        except:
                try:
                        ans =  request.environ['SSL_CLIENT_S_DN']
                except:
                        try:
                                ans = os.environ['DEMO_AUTH']
                        except:
                                ans = ''

        #If DN is that of the UI cert to API (MPO-UI-SERVER.crt), grab our special header for the user DN
	dn_dict = parse_dn(ans)
        #if cmp(dn_dict, server_dict) == 0:
	#	ans = request.headers.get('Real-User-DN')

        if dn_dict['CN']=='MPO-UI-SERVER':
		ans = request.headers.get('Real-User-DN')

        #JCW
        #if dn_dict is empty, this fails. IE if DEMO_AUTH not set, SSL_CLIENT_S_DN and HTTPS_DN not present
        #for DEMO user, api requests from UI have Real-User-DN set
        #print('AUTHDEBUG: in get_user_dn: cmp: ',str(dn_dict), str(server_dict), str(cmp(dn_dict, server_dict))  )
        #print('AUTHDEBUG: in get_user_dn ', ans, str(type(ans)),str(dn_dict),request.environ, os.environ )
        if ans=='':
            print('AUTHDEBUG: in get_user_dn FATAL, no user DN found in request:',request.environ,'headers',request.headers, request.headers['Real-User-DN'],str(type(request.headers)))

        return ans
