Steps for configuraing the apache web server for MPO
----------------------------------------------------

* Step 1. Install libapache2-mod-wsgi: 
>
>     apt-get install libapache2-mod-wsgi
>

* Step 2. Install Apache mod:
>
>     sudo a2enmod ssl
>

* Step 3. Activate apache mod:
>
>     sudo a2enmod rewrite 
>

* Step 4. Modify the the following items in Apache config file:
>
>     #security directives:
>
>     /etc/apache2/conf.d/security
>
>     #default directives
>
>     /etc/apache2/apache2.conf
>
>     #web server settings:
>
>     /etc/apache2/httpd.conf

* Step 5. Check/open needed ports: 
>
>     sudo lsof -i :8443
>
>     (please note that the web UI is on 443; API is on 443 and 8443.)
>

