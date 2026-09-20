# N32G415 系统时钟测量（PA8 / MCO）

在 N32G415 上测量系统时钟（SYSCLK）的推荐做法：通过 **MCO（Microcontroller Clock Output）** 将时钟波形从 **PA8** 硬件输出，再用示波器或频率计直接读取频率。

> 不要用软件 `GPIO` 翻转来测 SYSCLK——翻转频率受指令周期、Flash 等待、编译优化影响，结果不准确。

---

## 适用工程（Keil）

本方法适用于已包含国民技术（Nsing）固件库的 Keil 工程，典型结构如下：

| 分组 | 文件 | 作用 |
|------|------|------|
| STARTUP | `startup_n32g41x.s` | 启动文件 |
| CMSIS | `system_n32g41x.c` | 系统时钟初始化 |
| FWLB | `n32g41x_gpio.c` | 配置 PA8 |
| FWLB | `n32g41x_rcc.c` | 配置 MCO / SYSCLK |
| USER | `main.c` | 添加 MCO 初始化并调用 |

所需驱动已在 FWLB 中时，只需修改 `USER/main.c`。

---

## 原理说明

| 项目 | 说明 |
|------|------|
| 引脚 | **PA8** = MCO 输出脚 |
| GPIO 模式 | 复用推挽（`GPIO_Mode_AF_PP`） |
| 时钟源 | `SYSCLK`（也可选 HSI / HSE / PLL 做对比） |
| 测量方式 | 示波器探头接 **PA8** 与 **GND**，读方波频率 |
| 频率上限 | MCO 输出到 IO 时建议不超过约 **50 MHz**；SYSCLK 更高时需分频 |

若示波器读到频率为 \(f_{\text{MCO}}\)，分频比为 \(N\)，则：

\[
f_{\text{SYSCLK}} = f_{\text{MCO}} \times N
\]

---

## 推荐代码（写入 `main.c`）

```c
#include "main.h"
#include "log.h"
/* 按工程实际再包含其它头文件 */

/**
 * @brief  将 SYSCLK 经 MCO 输出到 PA8，供示波器测量
 */
void MCO_Config(void)
{
    GPIO_InitType GPIO_InitStructure;

    /* 1. 打开 GPIOA 时钟 */
    RCC_EnableAPB2PeriphClk(RCC_APB2_PERIPH_GPIOA, ENABLE);

    /* 2. PA8 配置为复用推挽、高速 */
    GPIO_InitStructure.Pin        = GPIO_PIN_8;
    GPIO_InitStructure.GPIO_Mode  = GPIO_Mode_AF_PP;
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
    GPIO_InitPeripheral(GPIOA, &GPIO_InitStructure);

    /* 若编译提示需要 AF 映射，取消下一行注释（宏名以 SDK 为准） */
    // GPIO_ConfigPinAF(GPIOA, GPIO_PIN_SOURCE8, GPIO_AF0_MCO);

    /* 3. 选择 MCO 时钟源为 SYSCLK */
    RCC_ConfigMco(RCC_MCO_SYSCLK);
    /* 部分 SDK 为两参数形式，例如：
     * RCC_ConfigMco(RCC_MCO_SYSCLK, RCC_MCO_DIV1);
     */
}

int main(void)
{
    /* 保持工程原有的 SystemInit / 日志 / 延时等初始化 */

    MCO_Config();

    while (1)
    {
        /* 应用逻辑 */
    }
}
```

### 宏名不一致时

在 Keil 中对 `RCC_ConfigMco` 按 **F12（Go To Definition）**，按 `n32g41x_rcc.h` 中的实际定义修改宏名。常见差异包括：

- `RCC_MCO_SYSCLK` / `RCC_MCO_SRC_SYSCLK`
- 单参数 `RCC_ConfigMco(src)` 或双参数 `RCC_ConfigMco(src, div)`

---

## SYSCLK 超过 50 MHz 时

N32G415 最高可运行到约 96 MHz。若 SYSCLK > 50 MHz，应对 MCO 分频后再输出，例如除以 2：

```c
/* 示例：宏名以你的 n32g41x_rcc.h 为准 */
RCC_ConfigMco(RCC_MCO_SYSCLK_DIV2);
/* 或 */
// RCC_ConfigMco(RCC_MCO_SYSCLK, RCC_MCO_DIV2);
```

示波器读到的是分频后频率，再乘回分频比得到真实 SYSCLK。

---

## 测量步骤

1. 编译、下载程序到 N32G415。
2. 示波器通道接地接板子 **GND**，探头接 **PA8**。
3. 设置为直流耦合，合适时基与触发电平，读取方波频率。
4. 与 `SystemCoreClock` 或时钟树配置对比，确认是否一致。

---

## 不推荐：软件翻转 PA8

仅作粗略观察时可用，**不能**当作频率计：

```c
void PA8_SoftwareToggle(void)
{
    GPIO_InitType GPIO_InitStructure;

    RCC_EnableAPB2PeriphClk(RCC_APB2_PERIPH_GPIOA, ENABLE);

    GPIO_InitStructure.Pin        = GPIO_PIN_8;
    GPIO_InitStructure.GPIO_Mode  = GPIO_Mode_Out_PP;
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
    GPIO_InitPeripheral(GPIOA, &GPIO_InitStructure);

    while (1)
    {
        GPIOA->POD ^= GPIO_PIN_8;  /* 或使用 GPIO_WriteBit / Toggle API */
    }
}
```

翻转频率大约为 `SYSCLK / (单次翻转指令周期 × 2)`，结果不可靠。

---

## 快速对照表

| 目标 | 做法 |
|------|------|
| 准确测量 SYSCLK | MCO → PA8 + 示波器 |
| 对比内部时钟 | MCO 源改为 HSI / HSE / PLL |
| SYSCLK > 50 MHz | 开启 MCO 分频后再测 |
| 粗看 IO 是否翻转 | 软件 Toggle（仅调试） |

---

## 参考

- N32G415 / N32G41x 用户手册：RCC → Clock Output (MCO)
- 固件库：`n32g41x_rcc.c` / `n32g41x_gpio.c`
- Keil 工程：在 `USER/main.c` 中调用 `MCO_Config()`
