# deploy

## install dependences and prepare

This project using `uv` to manage python environment.

On Debian/Ubuntu,youcan run this to install python3 and uv

```bash
sudo apt update
sudo apt install python3 uv
```

Then in the folder,making venv and active it,install the dependences

```bash
uv venv .
source .venv/bin/activate
uv pip install -r requirements.txt
```

Currently,we use gunicorn,nginx to deploy,install them with:

```bash
sudo apt install nginx
uv pip install gunicorn
```

## running

### set systemd (optional)

```bash
sudo nano /etc/systemd/system/blog-test.service
```

write something like this

```systemd
[Unit]
Description=Gunicorn instance for blog-test
After=network.target

[Service]
User=pi
Group=www-data
WorkingDirectory=/home/pi/blog-test
Environment="PATH=/home/pi/blog-test/.venv/bin"
ExecStart=/home/pi/blog-test/.venv/bin/gunicorn --workers 3 --bind unix:/var/www/blog-test/myapp.sock -m 007 app:app

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl start blog-test
sudo systemctl enable blog-test
sudo systemctl status blog-test # check status of running
```

### set nginx

there's example [`nginx.conf`](./nginx.conf),you can refer to it,or put it into `/etc/nginx/sites-available/blog-test` with your modification.

```bash
sudo ln -s /etc/nginx/site-available/blog-test /etc/nginx/sites-enabled
sudo nginx -t # check the conf file
sudo systemctl restart nginx
```
