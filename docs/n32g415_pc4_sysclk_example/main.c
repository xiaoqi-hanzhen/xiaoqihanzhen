/**
 * N32G415：PC4 紧循环翻转，示波器测系统时钟
 * 用法：替换 Keil USER/main.c，示波器接 PC4
 */
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

    /* 关中断，来回翻 PC4，尽量快、尽量稳 */
    __disable_irq();
    while (1)
    {
        GPIOC->PBSC = GPIO_PIN_4;
        GPIOC->PBC  = GPIO_PIN_4;
    }
}
