# N32G415 PA8 输出 SYSCLK（MCO）— 按官方 SDK 核对版

> 来源：Nsing `N32G41x-SDK` 官方例程  
> `projects/n32g41x_EVAL/examples/RCC/RCC_ClockConfig/`  
> 头文件：`n32g41x_rcc.h` / `n32g41x_gpio.h`

## 关键正确 API（N32G415）

| 项目 | 正确写法 |
|------|----------|
| MCO 引脚 | PA8 |
| 复用功能 | **GPIO_AF13**（N32G412 才是 GPIO_AF7） |
| GPIO 时钟 | `RCC_EnableAHBPeriphClk(RCC_AHB_PERIPH_GPIO, ENABLE)` |
| 模式 | `GPIO_MODE_AF_PP` |
| 上下拉 | `GPIO_NO_PULL` |
| 分频 | `RCC_ConfigMcoClkPre(RCC_MCO_CLK_DIVx)` |
| 时钟源 | `RCC_ConfigMco(RCC_MCO_SYSCLK)` |
| 官方限制 | **MCO 输出频率不要超过 20 MHz** |

时钟源宏：`RCC_MCO_NOCLK` / `RCC_MCO_LSI` / `RCC_MCO_LSE` / `RCC_MCO_SYSCLK` / `RCC_MCO_HSI` / `RCC_MCO_HSE` / `RCC_MCO_PLLDIV`

分频宏：`RCC_MCO_CLK_DIV1` / `DIV2` / `DIV4` / `DIV8` / `DIV16`

频率换算：

```text
真实 SYSCLK = 示波器读到的 MCO 频率 × 分频比
例：SYSCLK=72MHz，DIV8 → 示波器约 9MHz
```

---

## 复制到 `main.c`（推荐）

把下面函数加进你的工程，在 `main()` 里调用即可。  
默认按 **72 MHz SYSCLK → DIV8** 输出（官方例程同样用法）。若你主频不同，改分频。

```c
#include "main.h"
#include "log.h"

/* N32G415: PA8 = MCO, AF13 */
#define MCO_PIN   GPIO_PIN_8
#define MCO_GPIO  GPIOA
#define MCO_AF    GPIO_AF13

/**
 * @brief  PA8 输出时钟（MCO）
 * @note   官方要求：MCO 输出频率不要超过 20MHz
 *         源可选：RCC_MCO_SYSCLK / HSI / HSE / PLLDIV / LSI / LSE
 *         分频：  RCC_MCO_CLK_DIV1/2/4/8/16
 */
void MCO_Configuration(uint32_t MCO_source, uint32_t MCO_prescaler)
{
    GPIO_InitType GPIO_InitStructure;

    /* 1. 打开 GPIO 时钟（N32G41x 在 AHB，不是 APB2） */
    RCC_EnableAHBPeriphClk(RCC_AHB_PERIPH_GPIO, ENABLE);

    /* 2. PA8 复用推挽 -> MCO */
    GPIO_InitStruct(&GPIO_InitStructure);
    GPIO_InitStructure.Pin            = MCO_PIN;
    GPIO_InitStructure.GPIO_Mode      = GPIO_MODE_AF_PP;
    GPIO_InitStructure.GPIO_Pull      = GPIO_NO_PULL;
    GPIO_InitStructure.GPIO_Alternate = MCO_AF;
    GPIO_InitPeripheral(MCO_GPIO, &GPIO_InitStructure);

    /* 3. 先设分频，再选源 */
    RCC_ConfigMcoClkPre(MCO_prescaler);
    RCC_ConfigMco(MCO_source);
}

int main(void)
{
    /* 保持你工程原有时钟初始化（SystemInit 等）不动 */

    /*
     * 测 SYSCLK：
     * - 若 SYSCLK ≈ 16MHz（HSI）：可用 DIV1 或 DIV2
     * - 若 SYSCLK ≈ 72MHz（PLL） ：用 DIV8，示波器约 9MHz，再 ×8
     * - 若 SYSCLK ≈ 80MHz（PLL） ：用 DIV8，示波器约 10MHz，再 ×8
     */
    MCO_Configuration(RCC_MCO_SYSCLK, RCC_MCO_CLK_DIV8);

    while (1)
    {
    }
}
```

### 分频怎么选（保证 MCO ≤ 20 MHz）

| 你的 SYSCLK | 建议分频 | 示波器大约读到 | 换算 |
|-------------|----------|----------------|------|
| 16 MHz（HSI） | `RCC_MCO_CLK_DIV1` 或 `DIV2` | 16 或 8 MHz | ×1 或 ×2 |
| 8 MHz（HSE） | `RCC_MCO_CLK_DIV1` | 8 MHz | ×1 |
| 72 MHz（PLL） | `RCC_MCO_CLK_DIV8` | 9 MHz | ×8 |
| 80 MHz（PLL） | `RCC_MCO_CLK_DIV8` | 10 MHz | ×8 |

---

## 测量

1. 编译下载  
2. 示波器探头接 **PA8**，地接 **GND**  
3. 读频率，再乘分频比 = 真实 SYSCLK  

---

## 和错误写法对照（之前容易写错）

| 错误（不符合 N32G415 SDK） | 正确 |
|----------------------------|------|
| `RCC_EnableAPB2PeriphClk(GPIOA, ...)` | `RCC_EnableAHBPeriphClk(RCC_AHB_PERIPH_GPIO, ENABLE)` |
| `GPIO_Mode_AF_PP` / `GPIO_Speed_50MHz` | `GPIO_MODE_AF_PP` + `GPIO_Alternate = GPIO_AF13` |
| 只用 `RCC_ConfigMco(...)` | 先 `RCC_ConfigMcoClkPre`，再 `RCC_ConfigMco` |
| AF0 / AF8 | **N32G415 用 GPIO_AF13** |
| 说 IO 上限 50 MHz | 官方例程注明 **MCO ≤ 20 MHz** |
