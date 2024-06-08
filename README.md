<!--
SPDX-FileCopyrightText: 2015-2021 Rémy Roy

SPDX-License-Identifier: MIT
-->



<div align="center">

# CDDA 游戏启动器
[ [English](README_en.md) | 简体中文]

</div>

带有额外功能的 [Cataclysm: Dark Days Ahead](https://cataclysmdda.org/) 游戏启动器。

关注[Doiiars](https://space.bilibili.com/1036711705)的[Bilibili 账号](https://space.bilibili.com/1036711705)，后续可能在Bilibili上更新视频教程。

**(交流反馈QQ群：[491708665 (一键加群)](http://qm.qq.com/cgi-bin/qm/qr?_wv=1027&k=h30pFZuOws8XtP9kR13807pV9PsQQ_Gn&authKey=82bXfkY29udyKMXwVd6B2bd%2BOrsIo8rtPx7myJFH%2Fjhh%2BO5pNJlDqtZBo4wXM7R3&noverify=0&group_code=491708665))**

![GitHub 工作流状态（master 分支）](https://img.shields.io/github/actions/workflow/status/DoiiarX/CDDA-Game-Launcher/build.yml?branch=master)
![GitHub 工作流状态（develop 分支）](https://img.shields.io/github/actions/workflow/status/DoiiarX/CDDA-Game-Launcher/build.yml?branch=develop)

![GitHub 发布（按日期最新）](https://img.shields.io/github/v/release/DoiiarX/CDDA-Game-Launcher)
![GitHub 所有发布版本](https://img.shields.io/github/downloads/DoiiarX/CDDA-Game-Launcher/total)
[![GitHub 分叉](https://img.shields.io/github/forks/DoiiarX/CDDA-Game-Launcher)](https://github.com/DoiiarX/CDDA-Game-Launcher/network)
[![REUSE 状态](https://api.reuse.software/badge/github.com/DoiiarX/CDDA-Game-Launcher)](https://api.reuse.software/info/github.com/DoiiarX/CDDA-Game-Launcher)

[在此下载](https://github.com/DoiiarX/CDDA-Game-Launcher/releases)。

## ~~不再~~维护

~~此应用程序的维护和支持现已结束。您可能仍然可以使用它，但不提供任何保证。随意地分叉、修改、重建或随您所愿。~~

此应用程序的维护和支持已以_**有限的能力**_恢复。在我更多地了解启动器代码库_以及游戏本身_之前，期望主要是修复我在我的 CDDA 游戏过程中遇到的错误。

仍然欢迎并鼓励提交错误报告和功能请求，同时默认我可能无法处理所有请求，直到我对游戏和启动器更加熟悉。

目前，中文版由Doiiars提供维护。

## 更新计划
[查看更新计划](update_plan.md)

## 已实现的功能

* 启动游戏
* 检测游戏版本和构建号
* 检索可用的更新构建
* 在保留用户修改的同时自动更新游戏
* 声音包管理器
* 模组管理器
* 存档备份和自动备份
* 字体预设

## ~~计划的功能~~

* ~~图块集管理器~~


短期内没有计划的功能，只有维护和错误修复。尽管拥有图块集管理器确实很好，但对于一个刚刚从坟墓中复活的项目来说，可能是一个过于宏大的范围。我们拭目以待。

## 常见问题解答

### 之前的 CDDA 游戏启动器怎么了？

它已经不再维护。尽管如此，[remyroy](https://github.com/remyroy) 和 [其他贡献者](https://github.com/remyroy/CDDA-Game-Launcher/graphs/contributors) 的工作应得到赞扬和感激，他们迄今为止对启动器的工作，以及免费为 CDDA 社区提供如此有用的工具。

### 我的上一个版本在哪里？

它存储在游戏目录内的 `previous_version` 目录中。

### 启动器如何更新我的游戏？

* 启动器下载新版本的存档。
* 如果 `previous_version` 子目录存在，启动器会将其移到回收站。
* 启动器将游戏目录中的所有内容移动到 `previous_version` 子目录。
* 启动器在游戏目录中提取下载的存档。
* 启动器检查 `previous_version` 目录中的内容，并将从 `previous_version` 目录复制到真实游戏目录的存档、模组、图块集、声音包和许多其他有用文件，这些文件在下载的存档中缺失。它将假设下载的存档中包含的模组是最新和最新版本，并通过比较它们的唯一识别值来保留这些。

### 我认为启动器刚刚删除了我的文件。我该怎么办？

启动器非常注意不删除对您可能重要的任何文件。在默认和推荐的设置下，启动器总是移动文件而不是删除它们。如果您认为在更新过程中丢失了文件，请检查 `previous_version` 子目录。那里是您应该能够找到之前游戏版本的地方。您还可以检查回收站中的文件。这些是文件被移动的主要两个地方，您应该能在那里找到它们。

### 我的杀毒软件将启动器检测为威胁。我该怎么办？

较差的杀毒软件会将启动器检测为威胁，并阻止其执行或删除启动器。一个简单的解决办法是将启动器二进制文件添加到您的杀毒软件白名单中，或在检测到时选择信任此二进制文件的操作。

如果您感到偏执，您可以自己检查源代码并从源代码构建启动器。即使这样，您仍然可能会收到误报。作为软件开发人员，我们对此几乎无能为力。我们有[一份很好的构建指南](https://github.com/DoiiarX/CDDA-Game-Launcher/blob/master/BUILDING.md)供那些想要从源代码构建启动器的人参考。

许多人都想知道为什么杀毒软件会将启动器识别为威胁。已经有很多猜测试图找出这一问题的根本原因。最好的方法是询问那些杀毒软件开发商。不幸的是，出于许多充分的理由，他们不太可能作出回应。我们也可以对此进行几天的推测。我们目前最好的推测是因为我们使用了一个名为 PyInstaller 的组件[通常被标记为威胁](https://github.com/pyinstaller/pyinstaller/issues/4633)。现在，如果您想看看这个兔子洞有多深，您可以继续搜索或推测为什么 PyInstaller 本身通常被标记为威胁。留给读者做这项研究。

许多人还在问为什么不简单地向这些杀毒软件报告启动器是误报。我们欢迎任何愿意花时间这样做的人，但我们认为这主要是无效的。这些过程通常既耗时又被忽略。每次我们发布新版本，或者我们使用的组件更新或更改时，也必须重新进行这些过程。目前 PC 上的威胁检测状态非常混乱和令人遗憾，尤其是对于使用*免费*杀毒软件的所有人。

### 我在游戏本身发现了问题，或者我想为游戏本身提出建议。我该怎么办？

您应该[联系游戏开发者](https://cataclysmdda.org/#ive-found-a-bug--i-would-like-to-make-a-suggestion-what-should-i-do)。我们主要提供一个帮助游戏的工具。我们无法为游戏本身提供支持。

### 如何更新到新版本的游戏启动器？

启动器将在启动时自动检查更新版本。如果找到了，启动器会提示您更新。您始终可以在 [github 上下载最新版本](https://github.com/DoiiarX/CDDA-Game-Launcher/releases)。使用便携版的用户将必须手动下载和手动更新启动器。从帮助菜单中，您还可以检查新的更新。

### 启动器启动时一直崩溃。我该怎么办？

您可能需要删除配置文件以解决此问题。该文件名为 `configs.db`，位于 `%LOCALAPPDATA%\CDDA Game Launcher\`。一些用户报告并遇到了不相关的启动问题。在某些情况下，运行启动器的调试版本以获取更多日志可能有助于定位问题。[在此创建问题](https://github.com/DoiiarX/CDDA-Game-Launcher/issues)可能是解决问题的方法。

### 我刚安装了游戏，它已经有了一大堆模组。有问题吗？

基础游戏捆绑了大量模组。您可以将它们视为在游戏中创建新世界时可以激活或忽略的模块。这些模组或模块可以通过添加新物品、建筑、怪物、禁用某些游戏机制或改变您的游戏方式，提供不同的游戏体验。它们是使用相同游戏引擎进行独特游玩体验的简单方法。没有任何这些额外模组，或者在创建新世界时使用默认模组，游戏也非常有趣。如果您是游戏新手，建议您在首次游玩时避免使用额外模组，以熟悉游戏机制。一旦您熟悉了游戏，经过一次或几次游玩后，我建议您在下一个世界中回顾基础游戏模组甚至一些外部模组。

### 存储库中的模组损坏或启用时导致我的游戏崩溃。我该怎么办？

游戏更新经常会破坏模组，特别是在实验分支上。您可以尝试查看该模组是否有更新。您可以尝试通过删除并重新安装它来更新该模组。您可以尝试联系模组作者并要求他更新他的模组。

为不断扩展和变化的基础游戏维护外部模组可能是一项艰巨的任务。确保有良好工作模组的唯一确定和*官方*方法是将它们包含在基础游戏中。如果您关心可靠的游戏体验，您应该考虑仅使用基础游戏模组，并考虑使用稳定分支。

如果您发现存储库中的模组明显被遗弃且不再工作，请[打开一个问题](https://github.com/DoiiarX/CDDA-Game-Launcher/issues)，以便将其移除。

### 您会制作 Linux 或 macOS 版本吗？

很可能不会。您可以查看[Linux 问题](https://github.com/DoiiarX/CDDA-Game-Launcher/issues/329)和[Mac 问题](https://github.com/DoiiarX/CDDA-Game-Launcher/issues/73)了解更多信息。

### 它不起作用？您能帮我吗？

在 [Github 上提交您的问题](https://github.com/DoiiarX/CDDA-Game-Launcher/issues)。尝试[有效地报告错误](http://www.chiark.greenend.org.uk/~sgtatham/bugs.html)。

## 构建

您可以通过查看我们的[构建指南](BUILDING.md)了解如何运行和构建启动器。

## 许可证

本项目根据 [the MIT license](LICENSE) 的条款授权。

[启动器图标](cddagl/resources/launcher.ico)的使用许可由 [Paul Davey aka Mattahan](http://mattahan.deviantart.com/) 授予。

## 为此项目贡献

欢迎任何人参与贡献。请花一点时间审查[贡献指南](CONTRIBUTING.md)。

* [错误报告](CONTRIBUTING.md#bugs)
* [功能请求](CONTRIBUTING.md#features)
* [拉取请求](CONTRIBUTING.md#pull-requests)
* [翻译贡献](CONTRIBUTING.md#translations)

## 行为准则

参与此项目的人员应遵循[行为准则](CODE_OF_CONDUCT.md)。
