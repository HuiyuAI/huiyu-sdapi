# 绘语AI

<p align="center">
    <img src="./docs/icon.png" alt="Huiyu logo" style="width: 200px; height: 200px">
</p>
<p align="center">
    <img src="https://img.shields.io/badge/Python-3.10-blue">
    <img src="https://img.shields.io/badge/license-MIT-blue">
    <img src="https://hits.seeyoufarm.com/api/count/incr/badge.svg?url=https%3A%2F%2Fgithub.com%2FHuiyuAI%2Fhuiyu-cloud&count_bg=%2344CC11&title_bg=%23555555&title=hits&edge_flat=false">
</p>




## 绘语AI 是什么？

绘语AI是一套面向普通用户，提供 Stable Diffusion AI绘画功能的程序，现已支持微信小程序端，并有完善的Web后台管理界面。

模块结构分为：

- **SD调用端（对接 Stable Diffusion API 的程序） - 本仓库**
- [后端服务](https://github.com/HuiyuAI/huiyu-cloud)
- [uniapp用户端（已支持微信小程序）](https://github.com/HuiyuAI/huiyu-uniapp)
- [Web后台管理](https://github.com/HuiyuAI/huiyu-web-admin)



## 功能预览

参见[后端服务](https://github.com/HuiyuAI/huiyu-cloud)



## 功能特性

参见[后端服务](https://github.com/HuiyuAI/huiyu-cloud)



## 快速开始

> [!NOTE]
>
> 如需完整运行所有模块，强烈建议有 Stable Diffusion 相关的安装、使用经验者尝试
>
> 以下仅包括**SD调用端 - 本仓库**的运行方式，其它模块请看：
>
> - [后端服务](https://github.com/HuiyuAI/huiyu-cloud)
> - [uniapp用户端](https://github.com/HuiyuAI/huiyu-uniapp)
> - [Web后台管理](https://github.com/HuiyuAI/huiyu-web-admin)

>[!NOTE]
>
>本模块主要功能：
>
>- 接收后端服务生成图片的请求
>- 与 Stable Diffusion API 交互生成图片
>- 上传经无损压缩后的图片至云存储
>- 返回图片链接至后端服务
>
>如果你本地有强悍的GPU，本模块可本地运行（如果后端服务部署在服务器上，可借助内网穿透将本模块与服务器打通，参见[本地部署最佳实践](https://github.com/HuiyuAI/huiyu-cloud#本地部署最佳实践)）
>
>同样也适用于云GPU平台，但需确认开放外网访问，因为需要与后端服务通信以及向云存储服务上传生成的图片

1. 本模块通常与 Stable Diffusion 运行在同一台机器上，首先需要确保 SD 启用了 API 功能
   1. Windows 系统在 SD 目录下的 `webui-user.bat` 文件中，修改 `COMMANDLINE_ARGS`，增加 `--api` 选项
   2. Linux 系统 `bash webui.sh --nowebui`
2. SD 需要安装插件 [adetailer](https://github.com/Bing-su/adetailer)，并需要用到模型 `face_yolov8n.pt` ，请自行搜索对应教程
3. 安装依赖

```sh
pip install - r requirements.txt
```

4. 修改 `config.ini` 中的配置
5. 运行 `main.py`

```sh
python main.py
```





## 常见问题

参见[后端服务](https://github.com/HuiyuAI/huiyu-cloud)



## LICENSE

[MIT](https://github.com/HuiyuAI/huiyu-sdapi/blob/master/LICENSE)





















