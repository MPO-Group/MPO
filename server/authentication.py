def get_user_dn(request):
#        import getpass
        try:
                ans = request.environ['HTTPS_DN']
        except:
                try:
                        ans =  request.environ['SSL_CLIENT_S_DN']
                except:
                        try:
                                ans = request.environ['DEMO_AUTH']
                        except:
                                ans = ''

        #If DN is that of the UI cert to API (MPO-UI-SERVER.crt), grab our special header for the user DN
        if ans.find('abla@fusion.gat.com')>-1:
		ans = request.headers['Real-User-DN'] 
#        if len(ans) == 0:
#                ans = getpass.getuser()
        #print('debug get user dn',ans,str(request.environ))
        return ans
