
# AstrBot 库街区签到插件

![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

一个基于 AstrBot 的库街区自动签到插件，支持社区签到和游戏签到（鸣潮、战双等）。

## ✨ 功能特性

- 🔐 **用户绑定** - 支持多用户绑定各自的库街区 token
- 🎯 **手动签到** - 用户可随时手动触发签到
- 🔄 **自动签到** - 每天早上 7:00 自动为所有绑定用户执行签到
- 📊 **状态查询** - 查看 token 有效性和用户信息
- 🔔 **错误处理** - 完善的错误处理和用户友好提示

## 📦 安装

将插件目录复制到 AstrBot 的插件目录：

```bash
# 克隆仓库
git clone https://github.com/akongkkkk/astrbot_plugin_kjqqd.git

# 复制插件到 AstrBot 插件目录
cp -r astrbot_plugin_kjqqd/data/plugins/astrbot_plugin_kjqqd /path/to/astrbot/data/plugins/
```

## 🚀 使用方法

### 指令列表

| 指令 | 说明 | 示例 |
|------|------|------|
| `/kjq login <手机号> <验证码>` | 登录并绑定（会顶掉APP登录） | `/kjq login 13800138000 123456` |
| `/kjq bind <token>` | 手动绑定库街区 token（推荐） | `/kjq bind abc123xyz` |
| `/kjq unbind` | 解除绑定 | `/kjq unbind` |
| `/kjq sign` | 手动执行签到（显示获得道具） | `/kjq sign` |
| `/kjq status` | 查看 token 状态 | `/kjq status` |
| `/kjq help` | 显示帮助信息 | `/kjq help` |

### 获取 Token

**推荐方式：手动绑定**

1. 在手机上用手机号登录库街区 APP
2. 通过抓包工具获取请求头中的 `token` 字段
3. 使用 `/kjq bind <token>` 绑定

> ⚠️ **注意事项**：使用 `/kjq login` 命令会顶掉手机 APP 的登录状态，建议使用 `/kjq bind` 命令手动绑定。

## 📁 项目结构

```
astrbot_plugin_kjqqd/
├── metadata.yaml          # 插件元数据
├── main.py                # 插件入口（指令注册）
├── requirements.txt       # 依赖声明
├── kuro_config.py         # 用户 token 配置管理
├── kuro_api.py            # 库街区 API 封装层
├── kuro_sign.py           # 签到核心逻辑
└── README.md              # 项目说明文档
```

## 🛠️ 技术栈

- **Python 3.9+** - 开发语言
- **aiohttp** - 异步 HTTP 请求
- **AstrBot SDK** - 插件框架

## 📝 配置

插件无需额外配置，用户通过聊天指令绑定 token 即可使用。

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE)

## 🙏 感谢

本项目的开发参考了以下优秀项目：

1. **Kuro-API-Collection** by [TomyJan](https://github.com/TomyJan)
   - GitHub: https://github.com/TomyJan/Kuro-API-Collection
   - 提供了库街区 API 的详细文档

2. **kurobbs_auto_checkin** by [leeezep](https://github.com/leeezep)
   - GitHub: https://github.com/leeezep/kurobbs_auto_checkin
   - 提供了完整的签到实现参考

3. **Kuro-autosignin** by [mxyooR](https://github.com/mxyooR)
   - GitHub: https://github.com/mxyooR/Kuro-autosignin
   - 提供了签到流程的架构参考

4. **AstrBot** by [AstrBotDevs](https://github.com/AstrBotDevs)
   - GitHub: https://github.com/AstrBotDevs/AstrBot
   - 提供了强大的插件框架

感谢这些开源项目的作者们！

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📧 联系方式

如有问题或建议，欢迎在 GitHub 上提交 Issue。
