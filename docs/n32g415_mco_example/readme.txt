1、功能说明
    此例程演示配置不同的系统时钟源，并通过MCO引脚输出时钟信号。
    支持三种系统时钟源配置：
        方式1：HSI作为系统时钟（16MHz）
        方式2：HSE作为系统时钟（8MHz）
        方式3：PLL作为系统时钟（时钟源可选HSI或HSE，系统时钟频率可选80MHz或72MHz）
    配置完成后通过串口输出SYSCLK、HCLK、PCLK1、PCLK2频率信息。
    MCO引脚（PA8）输出选择系统时钟分频值。

2、使用环境
    芯片支持：
        N32G412x8L7
        N32G412xBL7
        N32G415x8L7
        N32G415xBL7
    软件环境：
        - Keil MDK-ARM V5.34
        - IAR EWARM V8.50.1

3、使用说明
    系统配置
        USART：TX - PA9，波特率115200
        GPIO：PA8 - 复用为MCO时钟输出

    使用方法：
        1、修改main.h中SYSCLK_SOURCE_SELECT选择时钟源
        2、编译并烧录程序
        3、通过串口助手查看时钟频率信息
        4、用示波器测量PA8引脚输出的MCO时钟波形

4、注意事项
    无


1. Function description
    This example demonstrates how to configure different system clock sources and output clock signals via the MCO pin.
    Three system clock source configurations are supported:
        Mode 1: HSI as the system clock (16 MHz)
        Mode 2: HSE as the system clock (8 MHz)
        Mode 3: PLL as the system clock (clock source can be HSI or HSE; system clock frequency can be 80 MHz or 72 MHz)
    After configuration, the frequencies of SYSCLK, HCLK, PCLK1, and PCLK2 are output via the serial port.
    The MCO pin (PA8) outputs the selected system clock division value.

2. Use environment
    Chip support: 
        N32G412x8L7
        N32G412xBL7
        N32G415x8L7
        N32G415xBL7
    Software Environment:
        - Keil MDK-ARM V5.34
        - IAR EWARM V8.50.1

3. Instructions for use
    System Configuration
        USART: TX - PA9, baud rate 115200
        GPIO: PA8 - Multiplexed as MCO clock output

    Usage Instructions:
        1. Modify the clock source selection in `SYSCLK_SOURCE_SELECT` within `main.h`
        2. Compile and flash the program
        3. View the clock frequency information using a serial port utility
        4. Measure the MCO clock waveform output on the PA8 pin using an oscilloscope

4. Attention
    None

