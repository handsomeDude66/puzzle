# AutoScript

项目分多个模块

## 仓库初始化

### proxy_pool 仓库初始化

```sh
./init.sh
```

### Python 仓库初始化

需要初始化 `AutoScript` 和 `Monitor` 仓库

需要安装 `pdm`, 并在对应仓库的目录下运行

```sh
pdm install
```

## 大麦监控

* 需要先启动代理池服务

启动 `proxy_pool`

```sh
./start.sh
```

停止 `proxy_pool`

```sh
./stop.sh
```

* 运行主程序

```sh
cd Monitor
pdm run src/monitor.py
```

## 猫眼监控

```sh
cd Monitor
pdm run src/maoyan_monitor.py
```
