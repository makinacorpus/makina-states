

```
88.86.85.96   88.5.5.5                      <-------
NET  ------------FBX-------------------- HOST ------- LXCBR1 |
                 10.6.1.254       10.6.1.1           10.5.0.1|
                                                             |---------|
                                                                    LXC 10.5.0.5
```

Allow forward
---------------
```
echo 'net.ipv4.ip_forward=1'>/etc/sysctl.d/99-forward.conf
sysctl --system
```

Masquerade public ip
---------------------
```
firewall-cmd --permanent --zone=lxc --set-target=ACCEPT
```

Identify and allow lxc traffic
--------------------------------
```
firewall-cmd --add-zone=lxc --permanent
firewall-cmd --permanent --zone=lxc --add-interface=lxcbr1
firewall-cmd --permanent --zone=lxc --set-target=ACCEPT
```

Reload firewall
---------------------
```
firewall-cmd --reload
```
