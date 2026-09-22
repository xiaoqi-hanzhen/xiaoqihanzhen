# N32G415 用 PC4 测系统时钟（简易版）

N32G415 硬件 MCO 只能出在 **PA8**。要用 **PC4** 测时钟，就把它配成推挽输出，关中断后死循环翻转，示波器接 PC4。

## 用法

把下面代码贴进 `main.c`（工程里已有 `SystemInit` / 库文件即可）：

```c
#include "n32g41x.h"
#include "n32g41x_rcc.h"
#include "n32g41x_gpio.h"

int main(void)
{
    GPIO_InitType g;

    RCC_EnableAHBPeriphClk(RCC_AHB_PERIPH_GPIO, ENABLE);

    GPIO_InitStruct(&g);
    g.Pin            = GPIO_PIN_4;
    g.GPIO_Mode      = GPIO_MODE_OUTPUT_PP;
    g.GPIO_Pull      = GPIO_NO_PULL;
    g.GPIO_Current   = GPIO_DS_HIGH;
    g.GPIO_Alternate = GPIO_NO_AF;
    GPIO_InitPeripheral(GPIOC, &g);

    __disable_irq();
    while (1)
    {
        GPIOC->PBSC = GPIO_PIN_4; /* 高 */
        GPIOC->PBC  = GPIO_PIN_4; /* 低 */
    }
}
```

## 测量

1. 示波器探头接 **PC4**，地接 **GND**
2. 读到的方波频率 ≈ `SYSCLK / 周期指令数`（紧循环大约几个周期翻一次）
3. 要硬件精确输出 SYSCLK，改用 **PA8 MCO**（见 `docs/n32g415_mco_example/`）

可直接用的源文件：`docs/n32g415_pc4_sysclk_example/main.c`
