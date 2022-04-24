# What is this project?
This is a project to remotely host a Mindustry server on a remote server without a GUI, such as AWS EC2 or Digital Ocean Droplets. 
It provides a simple web interface, where users can log in to issue simple commands.

# Mindustry Setup (Linux Server)
The following tutorial for setup assumed you have a Ubuntu server with Nginx and python3 installed. If your situation differs, your mileage may vary. Feel free to open an issue to ask for help.
A tutorial for installing Nginx can be found [here](https://www.digitalocean.com/community/tutorials/how-to-install-nginx-on-ubuntu-18-04).

1. `ssh` into your remote server.
2. `mkdir Mindustry && cd Mindustry` to make a folder for the code and server jar.
3. `wget https://github.com/LivelyCarpet87/Mindustry-HTTP-Wrapper/releases/download/v1.0/Mindustry-HTTP-Wrapper.zip` to download the latest release to the current folder.
4. `unzip -x Mindustry-HTTP-Wrapper.zip` to extract the files
5. `python3 -m venv mindustryServer` to create a virtual environment for the server's python dependency
6. `source mindustryServer/bin/activate` to activate the virtual environment. (You will need to do this step every time you start a new shell)
7. `pip3 install -r requirements.txt` to install the required libraries
8. `pip3 install gunicorn` to install `gunicorn` to host the server
9. `nano server.py` to open up the server file and edit the configuration section. 
Once complete, press `CTRL`+`O`, then `ENTER` to save the changes. 
Once complete, press `CTRL`+`X` to exit the editor. 
10. `sudo nano /etc/systemd/system/mindustry.service` to create a service file. This will launch the mindustry server everytime the virtual server starts.
11. Paste in and edit the following:
```
[Unit]
Description=Gunicorn instance to serve Mindustry
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/home/ubuntu/Mindustry
Environment="PATH=/home/ubuntu/Mindustry/mindustryServer/bin"
ExecStart=/home/ubuntu/Mindustry/mindustryServer/bin/gunicorn --workers 1 --threads 1 --bind unix:mindustry.sock -m 007 server:app

[Install]
WantedBy=multi-user.target
```
Once complete, press `CTRL`+`O`, then `ENTER` to save the changes. 
Once complete, press `CTRL`+`X` to exit the editor. 
12. `sudo systemctl start mindustry` to start the server
13. `sudo systemctl enable mindustry` to start the server on boot
14. `sudo systemctl status mindustry` to make sure everything is working fine. If errors occurred, check previous setps or open an issue to ask for help.
15. `sudo nano /etc/nginx/sites-available/mindustry` to create the Nginx server entry. Paste and edit the following as necessary.
```
server {
    listen 80;
    server_name your_domain_or_ip;

    location / {
        include proxy_params;
        proxy_pass http://unix:/home/ubuntu/Mindustry/mindustry.sock;
    }
}
```
Once complete, press `CTRL`+`O`, then `ENTER` to save the changes. 
Once complete, press `CTRL`+`X` to exit the editor. 
16. `sudo ln -s /etc/nginx/sites-available/mindustry /etc/nginx/sites-enabled` to link your site configuration to Nginx's enabled sites.
17. `sudo nginx -t` to check that everything is without issue with Nginx
18. `sudo systemctl restart nginx` to restart Nginx


# Predictable questions

## Why is the interface ugly?
Because this project does not need a beautiful interface to function, it is a collection of links that trigger different server responses. It currently does
not give any output back to the user interface because I still cannot get `pexpect` to parse the Mindustry CLI output. Instead, just look at your server to see
if anything happened.

## Why can't I issue any commands that requires input?
I believe that it is a horrible security practice to expose a web app that has priveleged access to a shell that can run arbitrary code, then hoping that it never
gets abused. Instead of investing in a lot of security filtering, I instead elected to whitelist inputs. Feel free to extend the code in any way to add more features,
or just open a pull request asking me to.