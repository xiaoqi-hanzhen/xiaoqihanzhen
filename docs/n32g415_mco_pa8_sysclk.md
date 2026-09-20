# N32G415 系统时钟测量完整指南（PA8 / MCO）

## 1. 目标

在 **N32G415** 上把系统时钟（`SYSCLK`）通过 **MCO** 从 **PA8** 引脚输出，用示波器或频率计直接测量实际频率，用于验证：

- PLL / HSE / HSI 配置是否正确
- `SystemCoreClock` 与真实频率是否一致
- 外设时钟分频是否符合预期

**推荐方式：MCO 硬件输出（准确）**  
**不推荐方式：软件 GPIO 翻转（不准确，仅作连通性调试）**

---

## 2. 适用 Keil 工程结构

本指南对应国民技术（Nsing）标准固件库 Keil 工程，典型工程树如下：

```text
N32G415 (Target)
├── STARTUP
│   └── startup_n32g41x.s
├── CMSIS
│   └── system_n32g41x.c          ← SystemInit / 系统时钟
├── FWLB
│   ├── n32g41x_gpio.c            ← 配置 PA8
│   ├── n32g41x_rcc.c             ← 配置 MCO
│   ├── n32g41x_usart.c
│   ├── n32g41x_flash.c
│   └── misc.c
├── USER
│   ├── main.c                    ← 在此添加 MCO_Config()
│   └── n32g41x_it.c
├── BSP
│   ├── log.c
│   └── delay.c
└── DOC
    └── readme.txt
```

需要的库文件：

| 文件 | 是否必须 | 作用 |
|------|----------|------|
| `n32g41x_gpio.c` | 是 | PA8 复用输出 |
| `n32g41x_rcc.c` | 是 | MCO 时钟源选择 / 分频 |
| `system_n32g41x.c` | 是 | 系统时钟初始化 |
| `main.c` | 是 | 调用初始化函数 |

> 若工程里已有上述文件，**只需改 `USER/main.c`**，不必再添加新驱动。

---

## 3. 原理说明

### 3.1 什么是 MCO

**MCO（Microcontroller Clock Output）** 把芯片内部时钟信号直接接到外部引脚。  
N32G415 上，MCO 默认对应 **PA8**。

可选输出源通常包括：

| MCO 源 | 含义 | 典型用途 |
|--------|------|----------|
| SYSCLK | 系统时钟 | 测主频（最常用） |
| HSI | 内部高速 RC | 核对内部振荡器 |
| HSE | 外部晶振 | 核对外部晶振是否起振 |
| PLL | PLL 输出 | 核对倍频结果 |
| LSI / LSE | 低速时钟 | 测 RTC / 低功耗相关时钟 |

### 3.2 引脚与电气要求

| 项目 | 要求 |
|------|------|
| 引脚 | **PA8** |
| GPIO 模式 | 复用推挽 `GPIO_Mode_AF_PP` |
| 速度 | 建议 `GPIO_Speed_50MHz` |
| 探头 | 示波器探头接 PA8，地线接 GND |
| 频率上限 | MCO 经 IO 输出时建议 **≤ 约 50 MHz** |

若 `SYSCLK` 高于约 50 MHz（例如 72 / 96 MHz），必须对 MCO **分频后再输出**，否则波形可能失真或测不准。

### 3.3 频率换算

示波器读到 MCO 频率为 \(f_{\text{MCO}}\)，分频比为 \(N\)：

\[
f_{\text{SYSCLK}} = f_{\text{MCO}} \times N
\]

示例：

| 配置 | 示波器读数 | 真实 SYSCLK |
|------|------------|-------------|
| SYSCLK，分频 1 | 48 MHz | 48 MHz |
| SYSCLK，分频 2 | 48 MHz | 96 MHz |
| HSE，分频 1 | 8 MHz | HSE = 8 MHz |

---

## 4. 完整代码（推荐：MCO 输出 SYSCLK）

把下面代码放入 `USER/main.c`（可按工程已有头文件微调）。

### 4.1 头文件

```c
#include "main.h"
#include "log.h"
#include "delay.h"
/* 若 main.h 未间接包含，可显式加上： */
/* #include "n32g41x.h" */
/* #include "n32g41x_rcc.h" */
/* #include "n32g41x_gpio.h" */
```

### 4.2 MCO 初始化函数

```c
/**
 * @brief  将 SYSCLK 经 MCO 输出到 PA8，供示波器测量
 * @note   若 SYSCLK > 50MHz，请改用带分频的配置（见 4.4）
 */
void MCO_Config(void)
{
    GPIO_InitType GPIO_InitStructure;

    /* 1. 打开 GPIOA 时钟（N32G415 上 GPIO 一般在 APB2） */
    RCC_EnableAPB2PeriphClk(RCC_APB2_PERIPH_GPIOA, ENABLE);

    /* 2. PA8 配成复用推挽、高速 */
    GPIO_InitStructure.Pin        = GPIO_PIN_8;
    GPIO_InitStructure.GPIO_Mode  = GPIO_Mode_AF_PP;
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
    GPIO_InitPeripheral(GPIOA, &GPIO_InitStructure);

    /*
     * 3. 若编译报错 / 波形没有输出，再配置 AF（宏以你 SDK 为准）
     *    在 Keil 中对 GPIO_ConfigPinAF / GPIO_AF0_MCO 按 F12 核对。
     */
    // GPIO_ConfigPinAF(GPIOA, GPIO_PIN_SOURCE8, GPIO_AF0_MCO);

    /* 4. 选择 MCO 源 = SYSCLK（无分频） */
    RCC_ConfigMco(RCC_MCO_SYSCLK);

    /*
     * 部分 SDK 是两参数形式，请二选一：
     * RCC_ConfigMco(RCC_MCO_SYSCLK, RCC_MCO_DIV1);
     * RCC_ConfigMco(RCC_MCO_SRC_SYSCLK, RCC_MCO_DIV_1);
     */
}
```

### 4.3 `main` 函数调用

```c
int main(void)
{
    /* 启动文件会先调用 SystemInit()，此处不要破坏原有时钟初始化顺序 */

    /* 可选：工程自带初始化 */
    // log_init();
    // delay_init();

    /* 输出 SYSCLK 到 PA8 */
    MCO_Config();

    /* 可选：打印软件认为的系统时钟，便于和示波器对比 */
    // log_info("SystemCoreClock = %lu Hz\r\n", (unsigned long)SystemCoreClock);

    while (1)
    {
        /* 业务逻辑；测量时保持运行即可 */
    }
}
```

### 4.4 SYSCLK 超过 50 MHz 时（必须分频）

N32G415 最高约 **96 MHz**。若主频高于约 50 MHz：

```c
void MCO_Config_Div2(void)
{
    GPIO_InitType GPIO_InitStructure;

    RCC_EnableAPB2PeriphClk(RCC_APB2_PERIPH_GPIOA, ENABLE);

    GPIO_InitStructure.Pin        = GPIO_PIN_8;
    GPIO_InitStructure.GPIO_Mode  = GPIO_Mode_AF_PP;
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
    GPIO_InitPeripheral(GPIOA, &GPIO_InitStructure);

    // GPIO_ConfigPinAF(GPIOA, GPIO_PIN_SOURCE8, GPIO_AF0_MCO);

    /* 方式 A：库里已有合在一起的宏 */
    RCC_ConfigMco(RCC_MCO_SYSCLK_DIV2);

    /* 方式 B：源 + 分频两参数（按你的头文件选择） */
    // RCC_ConfigMco(RCC_MCO_SYSCLK, RCC_MCO_DIV2);
}
```

示波器若读到 **48 MHz**，且分频为 2，则真实 `SYSCLK = 96 MHz`。

### 4.5 输出其它时钟源（可选）

用于排查晶振 / PLL：

```c
/* 输出 HSE（外部晶振） */
RCC_ConfigMco(RCC_MCO_HSE);

/* 输出 HSI（内部 RC） */
RCC_ConfigMco(RCC_MCO_HSI);

/* 输出 PLL */
RCC_ConfigMco(RCC_MCO_PLL);
```

> 具体宏名以 `n32g41x_rcc.h` 为准。在 Keil 中打开该头文件，搜索 `MCO` 即可看到全部枚举。

---

## 5. 宏名不一致时怎么改

不同版本固件库命名可能不同。处理步骤：

1. 在 `main.c` 里对 `RCC_ConfigMco` 按 **F12（Go To Definition）**
2. 打开 `n32g41x_rcc.h`，搜索 `MCO`
3. 把代码里的宏改成头文件里真实存在的名字

常见差异对照：

| 本文示例 | 可能的实际宏名 |
|----------|----------------|
| `RCC_MCO_SYSCLK` | `RCC_MCO_SRC_SYSCLK` / `RCC_MCOSource_SYSCLK` |
| `RCC_MCO_DIV1` | `RCC_MCO_DIV_1` / `RCC_MCOPrescaler_1` |
| `GPIO_Mode_AF_PP` | `GPIO_MODE_AF_PP`（少见，以库为准） |
| `GPIO_InitPeripheral` | `GPIO_Init`（旧命名） |
| `RCC_EnableAPB2PeriphClk` | `RCC_APB2PeriphClockCmd`（旧命名） |

---

## 6. 测量步骤（示波器）

1. **编译并下载**程序到 N32G415（Keil：Rebuild → Download / F8）。
2. 确认程序在跑（可加 LED 翻转或串口打印确认 `main` 已进入）。
3. 示波器：
   - 探头接到 **PA8**
   - 地线夹接到板子 **GND**
   - 耦合方式选 **DC**
   - 时基先设到 `20 ns/div ~ 100 ns/div`（视频率调整）
   - 触发电平调到波形中间
4. 使用示波器 **Measure → Frequency** 读频率。
5. 若启用了分频，按第 3.3 节换算真实 `SYSCLK`。
6. 与软件变量对比：

```c
extern uint32_t SystemCoreClock;
/* 打印或在调试 Watch 窗口查看 SystemCoreClock */
```

---

## 7. 完整可复制示例（最小工程版）

下面是一份尽量完整、可直接粘贴到 `main.c` 的示例（保留版权头可按工程原样）：

```c
#include "main.h"
#include "log.h"

static void MCO_Config(void);

/**
 * @brief  MCO: SYSCLK -> PA8
 */
static void MCO_Config(void)
{
    GPIO_InitType GPIO_InitStructure;

    RCC_EnableAPB2PeriphClk(RCC_APB2_PERIPH_GPIOA, ENABLE);

    GPIO_InitStructure.Pin        = GPIO_PIN_8;
    GPIO_InitStructure.GPIO_Mode  = GPIO_Mode_AF_PP;
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
    GPIO_InitPeripheral(GPIOA, &GPIO_InitStructure);

    /* 需要时打开 AF 配置 */
    // GPIO_ConfigPinAF(GPIOA, GPIO_PIN_SOURCE8, GPIO_AF0_MCO);

    /*
     * SYSCLK <= 50MHz: 用 DIV1
     * SYSCLK >  50MHz: 改成 DIV2 / DIV4，并按分频换算
     */
    RCC_ConfigMco(RCC_MCO_SYSCLK);
    // RCC_ConfigMco(RCC_MCO_SYSCLK, RCC_MCO_DIV1);
    // RCC_ConfigMco(RCC_MCO_SYSCLK_DIV2);
}

int main(void)
{
    MCO_Config();

    while (1)
    {
    }
}

#ifdef USE_FULL_ASSERT
void assert_failed(const uint8_t* expr, const uint8_t* file, uint32_t line)
{
    (void)expr;
    (void)file;
    (void)line;
    while (1)
    {
    }
}
#endif
```

---

## 8. 不推荐：软件翻转 PA8（仅调试）

软件翻转只能粗看 IO 是否能动，**不能**准确代表 `SYSCLK`。

```c
/**
 * @brief  软件翻转 PA8（不准确，仅连通性测试）
 */
void PA8_SoftwareToggle(void)
{
    GPIO_InitType GPIO_InitStructure;

    RCC_EnableAPB2PeriphClk(RCC_APB2_PERIPH_GPIOA, ENABLE);

    GPIO_InitStructure.Pin        = GPIO_PIN_8;
    GPIO_InitStructure.GPIO_Mode  = GPIO_Mode_Out_PP; /* 注意：普通推挽，不是 AF */
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
    GPIO_InitPeripheral(GPIOA, &GPIO_InitStructure);

    while (1)
    {
        GPIOA->POD ^= GPIO_PIN_8;
        /* 或：
         * GPIO_WriteBit(GPIOA, GPIO_PIN_8, Bit_SET);
         * GPIO_WriteBit(GPIOA, GPIO_PIN_8, Bit_RESET);
         */
    }
}
```

估算关系（仅供参考）：

\[
f_{\text{翻转}} \approx \frac{f_{\text{SYSCLK}}}{T_{\text{单次翻转指令周期}} \times 2}
\]

受编译优化等级、Flash wait state、是否开 Cache 影响很大，**不要用来标定主频**。

---

## 9. 常见问题排查

| 现象 | 可能原因 | 处理 |
|------|----------|------|
| PA8 无波形 | 未调 `MCO_Config()` | 确认 `main` 里已调用 |
| PA8 无波形 | GPIO 未开时钟 / 模式不对 | 检查 `RCC_EnableAPB2PeriphClk` 与 `GPIO_Mode_AF_PP` |
| PA8 无波形 | 缺 AF 映射 | 打开 `GPIO_ConfigPinAF(...)` |
| 频率只有预期一半/两倍 | 分频配置不对 | 查 `MCOPRES` / `RCC_MCO_DIVx` |
| 频率不对且不稳定 | 探头地线太长 / 负载过大 | 地线尽量短；不要串大电容 |
| 高频波形三角化 | 超过 IO 能力 | 对 MCO 分频后再测 |
| 编译报宏未定义 | SDK 宏名不同 | F12 查 `n32g41x_rcc.h` 后改名 |
| 与 `SystemCoreClock` 差很多 | 时钟树配置错误 | 先查 `system_n32g41x.c` / HSE 值 |

---

## 10. 快速对照表

| 目标 | 做法 |
|------|------|
| 准确测 SYSCLK | MCO → PA8 + 示波器 |
| SYSCLK > 50 MHz | MCO 分频后再测，再乘回分频比 |
| 核对外部晶振 | MCO 源选 HSE |
| 核对内部 RC | MCO 源选 HSI |
| 核对 PLL | MCO 源选 PLL |
| 只测 PA8 是否能翻转 | 软件 Toggle（不可用于测频） |

---

## 11. 操作检查清单

- [ ] 工程已加入 `n32g41x_gpio.c`、`n32g41x_rcc.c`
- [ ] `main.c` 已添加并调用 `MCO_Config()`
- [ ] PA8 为复用推挽，速度 50 MHz
- [ ] `RCC_ConfigMco` 宏已按本工程头文件核对
- [ ] SYSCLK > 50 MHz 时已设置分频
- [ ] 示波器探头接 PA8，地接 GND
- [ ] 读到的频率（× 分频）与 `SystemCoreClock` 一致

---

## 12. 参考

- N32G415 / N32G41x 用户手册：RCC → **Clock Output (MCO)**；GPIO → PA8 alternate function
- 固件库源文件：`n32g41x_rcc.c`、`n32g41x_gpio.c`
- CMSIS：`system_n32g41x.c`（`SystemInit`、`SystemCoreClock`）
- Keil 工程：在 `USER/main.c` 中调用 `MCO_Config()`

---

## 13. 版本信息

| 项目 | 内容 |
|------|------|
| 文档主题 | N32G415 PA8 MCO 测量 SYSCLK |
| 适用芯片 | N32G415 / N32G41x 系列 |
| 适用 IDE | Keil MDK-ARM（uVision） |
| 适用库 | Nsing / Nationz 标准外设库（FWLB） |
| 文档路径 | `docs/n32g415_mco_pa8_sysclk.md` |
