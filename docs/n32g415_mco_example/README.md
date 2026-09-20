# N32G415 MCO（PA8）完整程序

来源：Nsing 官方 `N32G41x-SDK` 例程 `RCC_ClockConfig`，已按 N32G415 核对。

## 文件

| 文件 | 作用 |
|------|------|
| `main.c` | 完整主程序：配置时钟 + PA8 输出 MCO |
| `main.h` | 头文件：MCO 引脚/AF、时钟源选择宏 |
| `n32g41x_it.c` / `n32g41x_it.h` | 中断文件（工程里已有可保留原文件） |
| `readme.txt` | 官方说明 |

## 用法

1. 用本目录的 `main.c`、`main.h` **替换** Keil 工程 `USER` 下同名文件  
2. 确认工程已加入：`n32g41x_gpio.c`、`n32g41x_rcc.c`、`n32g41x_flash.c`、`log.c`、`delay.c`  
3. 在 `main.h` 里选时钟源：

```c
#define SYSCLK_SOURCE_SELECT   SYSCLK_SOURCE_PLL   /* 或 HSI / HSE */
```

4. 编译下载；示波器接 **PA8** 与 **GND**  
5. 频率换算：`真实 SYSCLK = 示波器频率 × 分频比`  
   - PLL 72MHz → `DIV8` → 约 9 MHz  
   - HSI 16MHz → `DIV2` → 约 8 MHz  

## 注意

- 板子无 8MHz 外部晶振时，把 `SYSCLK_SOURCE_SELECT` 改成 `SYSCLK_SOURCE_HSI`  
- 用 HSE/PLL 时，`HSE_VALUE` 必须是 8000000  
- 官方要求：**MCO 输出 ≤ 20 MHz**
