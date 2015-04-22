def get_user_dn(request):
#        import getpass
        try:
                ans = request.environ['HTTPS_DN']
        except:
                try:
                        ans =  request.environ['SSL_CLIENT_S_DN']
                except:
                        ans = ''

        #If DN is that of the UI, grab our special header for the user DN
	if ans == '/C=US/ST=California/L=LaJolla/O=General Atomics/O=c21f969b5f03d33d43e04f8f136e7682/OU=GAT/CN=MPO-UI-SERVER/emailAddress=abla@fusion.gat.com' :
		ans = request.headers['Real-User-DN'] 
#        if len(ans) == 0:
#                ans = getpass.getuser()
        #print('debug get user dn',ans,str(request.environ))
        return ans
