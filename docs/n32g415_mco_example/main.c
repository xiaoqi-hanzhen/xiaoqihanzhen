/**
*     Copyright (c) 2025, Nsing Technologies Inc.
*
*     All rights reserved.
*
*     This software is the exclusive property of Nsing Technologies Inc. (Hereinafter
* referred to as Nsing). This software, and the product of Nsing described herein
* (Hereinafter referred to as the Product) are owned by Nsing under the laws and treaties
* of the People's Republic of China and other applicable jurisdictions worldwide.
*
*     Nsing does not grant any license under its patents, copyrights, trademarks, or other
* intellectual property rights. Names and brands of third party may be mentioned or referred
* thereto (if any) for identification purposes only.
*
*     Nsing reserves the right to make changes, corrections, enhancements, modifications, and
* improvements to this software at any time without notice. Please contact Nsing and obtain
* the latest version of this software before placing orders.

*     Although Nsing has attempted to provide accurate and reliable information, Nsing assumes
* no responsibility for the accuracy and reliability of this software.
*
*     It is the responsibility of the user of this software to properly design, program, and test
* the functionality and safety of any application made of this information and any resulting product.
* In no event shall Nsing be liable for any direct, indirect, incidental, special,exemplary, or
* consequential damages arising in any way out of the use of this software or the Product.
*
*     Nsing Products are neither intended nor warranted for usage in systems or equipment, any
* malfunction or failure of which may cause loss of human life, bodily injury or severe property
* damage. Such applications are deemed, "Insecure Usage".
*
*     All Insecure Usage shall be made at user's risk. User shall indemnify Nsing and hold Nsing
* harmless from and against all claims, costs, damages, and other liabilities, arising from or related
* to any customer's Insecure Usage.

*     Any express or implied warranty with regard to this software or the Product, including,but not
* limited to, the warranties of merchantability, fitness for a particular purpose and non-infringement
* are disclaimed to the fullest extent permitted by law.

*     Unless otherwise explicitly permitted by Nsing, anyone may not duplicate, modify, transcribe
* or otherwise distribute this software for any purposes, in whole or in part.
*
*     Nsing products and technologies shall not be used for or incorporated into any products or systems
* whose manufacture, use, or sale is prohibited under any applicable domestic or foreign laws or regulations.
* User shall comply with any applicable export control laws and regulations promulgated and administered by
* the governments of any countries asserting jurisdiction over the parties or transactions.
**/

/**
*\*\file      main.c
*\*\author    Nsing
*\*\version   v1.0.0
*\*\copyright Copyright (c) 2025, Nsing Technologies Inc. All rights reserved.
**/
#include "main.h"
#include "log.h"
#include "delay.h"

/** RCC_ClockConfig **/

RCC_ClocksType RCC_ClockFreq;

ErrorStatus SetSysClockToHSI(void);
ErrorStatus SetSysClockToHSE(void);
ErrorStatus SetSysClockToPLL(uint32_t PLL_src, uint32_t SYS_freq);
void MCO_Configuration(uint32_t MCO_source, uint32_t MCO_prescaler);

/**
*\*\name    PrintfClockInfo.
*\*\fun     Printf clock information.
*\*\param   msg
*\*\return  none
**/
void PrintfClockInfo(const char* msg)
{
    log_init(); /* should reinit after sysclk changed */
    log_info("\n--------------------------------\n");
    log_info("%s:\n", msg);
    RCC_GetClocksFreqValue(&RCC_ClockFreq);
    log_info("SYSCLK: %d\n", RCC_ClockFreq.SysclkFreq);
    log_info("HCLK: %d\n", RCC_ClockFreq.HclkFreq);
    log_info("PCLK1: %d\n", RCC_ClockFreq.Pclk1Freq);
    log_info("PCLK2: %d\n", RCC_ClockFreq.Pclk2Freq);
    SysTick_Delay_Ms(1);/* Waiting for the log transmission to complete */
}

/**
*\*\name    main.
*\*\fun     main function.
*\*\param   none
*\*\return  none
**/
int main(void)
{
    PrintfClockInfo("After reset");

/*** Select one of the following configuration methods ***/
#if SYSCLK_SOURCE_SELECT == SYSCLK_SOURCE_HSI
    /* Method 1: HSI as system clock (16MHz) */
    if (SetSysClockToHSI() == ERROR)
    {
        log_info("Clock configuration failure!\n");
    }
    PrintfClockInfo("HSI->SYSCLK, 16MHz");

    MCO_Configuration(RCC_MCO_SYSCLK, RCC_MCO_CLK_DIV2);

#elif SYSCLK_SOURCE_SELECT == SYSCLK_SOURCE_HSE
    /* Method 2: HSE as system clock (8MHz) */
    if (SetSysClockToHSE() == ERROR)
    {
        log_info("Clock configuration failure!\n");
    }
    PrintfClockInfo("HSE->SYSCLK, 8MHz");

    MCO_Configuration(RCC_MCO_SYSCLK, RCC_MCO_CLK_DIV1);

#elif SYSCLK_SOURCE_SELECT == SYSCLK_SOURCE_PLL
    /* Method 3: PLL as system clock (72MHz from HSE) */
    if (SetSysClockToPLL(RCC_PLL_SRC_HSE, 72000000U) == ERROR)
    {
        log_info("Clock configuration failure!\n");
    }
    PrintfClockInfo("HSE->PLL->SYSCLK, 72MHz");

    MCO_Configuration(RCC_MCO_SYSCLK, RCC_MCO_CLK_DIV8);
#endif

    while (1)
    {
    }
}

/**
*\*\name    MCO_Configuration.
*\*\fun     Configure MCO pin (PA8) and select clock source with prescaler.
*\*\param   MCO_source: 
*\*\         - RCC_MCO_NOCLK       No clock selected
*\*\         - RCC_MCO_LSI         LSI oscillator clock selected
*\*\         - RCC_MCO_LSE		   LSE oscillator clock selected
*\*\         - RCC_MCO_SYSCLK      System clock selected
*\*\         - RCC_MCO_HSI         HSI oscillator clock selected
*\*\         - RCC_MCO_HSE         HSE oscillator clock selected
*\*\         - RCC_MCO_PLLDIV      PLL sysdiv clock selected
*\*\param   MCO_prescaler: 
*\*\          - RCC_MCO_CLK_DIV1   
*\*\          - RCC_MCO_CLK_DIV2    
*\*\          - RCC_MCO_CLK_DIV4    
*\*\          - RCC_MCO_CLK_DIV8
*\*\          - RCC_MCO_CLK_DIV16
*\*\return  none
*\*\note    MCO output must not exceed 20MHz.
**/
void MCO_Configuration(uint32_t MCO_source, uint32_t MCO_prescaler)
{
    GPIO_InitType GPIO_InitStructure;

    /* Enable GPIO clock */
    RCC_EnableAHBPeriphClk(RCC_AHB_PERIPH_GPIO, ENABLE);

    /* Configure MCO pin as alternate push-pull */
    GPIO_InitStruct(&GPIO_InitStructure);
    GPIO_InitStructure.Pin            = MCO_PIN;
    GPIO_InitStructure.GPIO_Mode      = GPIO_MODE_AF_PP;
    GPIO_InitStructure.GPIO_Pull      = GPIO_NO_PULL;
    GPIO_InitStructure.GPIO_Alternate = MCO_AF;
    GPIO_InitPeripheral(MCO_GPIO, &GPIO_InitStructure);

    /* Configure MCO prescaler */
    RCC_ConfigMcoClkPre(MCO_prescaler);

    /* Select MCO clock source */
    RCC_ConfigMco(MCO_source);
}

/**
*\*\name    SetSysClockToHSI.
*\*\fun     Selects HSI as System clock source and configure HCLK, PCLK2 and PCLK1.
*\*\return  SUCCESS or ERROR
**/
ErrorStatus SetSysClockToHSI(void)
{
    uint32_t timeout_value = 0xFFFFFFFF;
    ErrorStatus ClockStatus;

    /* RCC system reset */
    FLASH_SetLatency(FLASH_LATENCY_2);
    RCC_DeInit();

    /* Enable HSI */
    RCC_EnableHsi(ENABLE);

    /* Wait till HSI is ready */
    ClockStatus = RCC_WaitHsiStable();

    if (ClockStatus == SUCCESS)
    {
        /* Enable Prefetch Buffer */
        FLASH_PrefetchBufSet(FLASH_PrefetchBuf_EN);

        /* Flash 0 wait state (HSI = 16MHz, <= 36MHz) */
        FLASH_SetLatency(FLASH_LATENCY_0);

        /* HCLK = SYSCLK */
        RCC_ConfigHclk(RCC_SYSCLK_DIV1);

        /* PCLK2 = HCLK */
        RCC_ConfigPclk2(RCC_HCLK_DIV1);

        /* PCLK1 = HCLK */
        RCC_ConfigPclk1(RCC_HCLK_DIV1);

        /* Select HSI as system clock source */
        RCC_ConfigSysclk(RCC_SYSCLK_SRC_HSI);

        /* Wait till HSI is used as system clock source */
        while (RCC_GetSysclkSrc() != RCC_SYSCLK_STS_HSI)
        {
            if ((timeout_value--) == 0)
            {
                return ERROR;
            }
        }
    }
    else
    {
        return ERROR;
    }
    return SUCCESS;
}

/**
*\*\name    SetSysClockToHSE.
*\*\fun     Selects HSE as System clock source and configure HCLK, PCLK2 and PCLK1.
*\*\return  SUCCESS or ERROR
**/
ErrorStatus SetSysClockToHSE(void)
{
    uint32_t timeout_value = 0xFFFFFFFF;
    ErrorStatus ClockStatus;

    /* RCC system reset */
    FLASH_SetLatency(FLASH_LATENCY_2);
    RCC_DeInit();

    /* Enable HSE */
    RCC_ConfigHse(RCC_HSE_ENABLE);

    /* Wait till HSE is ready */
    ClockStatus = RCC_WaitHseStable();

    if (ClockStatus == SUCCESS)
    {
        /* Enable Prefetch Buffer */
        FLASH_PrefetchBufSet(FLASH_PrefetchBuf_EN);

        /* Flash 0 wait state (HSE = 8MHz, <= 36MHz) */
        FLASH_SetLatency(FLASH_LATENCY_0);

        /* HCLK = SYSCLK */
        RCC_ConfigHclk(RCC_SYSCLK_DIV1);

        /* PCLK2 = HCLK */
        RCC_ConfigPclk2(RCC_HCLK_DIV1);

        /* PCLK1 = HCLK */
        RCC_ConfigPclk1(RCC_HCLK_DIV1);

        /* Select HSE as system clock source */
        RCC_ConfigSysclk(RCC_SYSCLK_SRC_HSE);

        /* Wait till HSE is used as system clock source */
        while (RCC_GetSysclkSrc() != RCC_SYSCLK_STS_HSE)
        {
            if ((timeout_value--) == 0)
            {
                return ERROR;
            }
        }
    }
    else
    {
        return ERROR;
    }
    return SUCCESS;
}

/**
*\*\name    SetSysClockToPLL.
*\*\fun     Selects PLL clock as System clock source and configure HCLK, PCLK2 and PCLK1.
*\*\param   PLL_src
*\*\         - RCC_PLL_SRC_HSI
*\*\         - RCC_PLL_SRC_HSE
*\*\param   SYS_freq
*\*\         - 72000000  (sysclk-72M, pll-144M, hclk-72M, pclk2-72M, pclk1-36M)
*\*\         - 80000000  (sysclk-80M, pll-80M, hclk-80M, pclk2-80M, pclk1-40M)
*\*\return  SUCCESS or ERROR
*\*\note    Fin frequency requirement is in the range of 8MHz ~ 32MHz,
*\*\	    Fvco(=Fin/pllinpre*pllmul) frequency requirement is in the range of 100MHz ~ 160MHz,
*\*\	    Fout(=Fvco/plloutdiv) frequency requirement is in the range of 64MHz ~ 160MHz. 
**/
ErrorStatus SetSysClockToPLL(uint32_t PLL_src, uint32_t SYS_freq)
{
    uint32_t timeout_value = 0xFFFFFFFF;
    ErrorStatus ClockStatus;
    uint32_t latency;
    uint32_t pllmul, pllinpre, plloutdiv;
    FunctionalState pllsysdiv;
    
    if ((PLL_src == RCC_PLL_SRC_HSE)&&(HSE_VALUE != 8000000))
    {
        /* HSE_VALUE == 8000000 is needed in this project! */
        return ERROR;
    }

    /* RCC system reset */
    FLASH_SetLatency(FLASH_LATENCY_2);
    RCC_DeInit();

    if (PLL_src == RCC_PLL_SRC_HSE)
    {
        /* Enable HSE */
        RCC_ConfigHse(RCC_HSE_ENABLE);

        /* Wait till HSE is ready */
        ClockStatus = RCC_WaitHseStable();
    }
    else
    {
        /* Enable HSI */
        RCC_EnableHsi(ENABLE);

        /* Wait till HSI is ready */
        ClockStatus = RCC_WaitHsiStable();
    }

    if (ClockStatus != SUCCESS)
    {
        return ERROR;
    }

    /* Configure PLL input prescaler based on clock source
     * HSI = 16MHz -> PLLINPRES = /4 -> 4MHz 
     * HSE = 8MHz  -> PLLINPRES = /2 -> 4MHz  */
    if (PLL_src == RCC_PLL_SRC_HSI)
    {
        pllinpre = 4;
    }
    else
    {
        pllinpre = 2;
    }

    switch (SYS_freq)
    {
        case 72000000:
            /* 4MHz * 36 = 144MHz(FVCO) / 1(PLLOD) /1 = 144MHz(Fpll) */
            latency   = FLASH_LATENCY_1;   /* 36MHz < SYSCLK <= 72MHz */
            pllmul    = 36;
            plloutdiv = RCC_PLL_OD_DIV_1;
            pllsysdiv = ENABLE;
            break;
        case 80000000:
            /* 4MHz * 40 = 160MHz(FVCO) / 2(PLLOD) /1 = 80MHz(Fpll) */
            latency   = FLASH_LATENCY_2;   /* 72MHz < SYSCLK <= 80MHz */
            pllmul    = 40;
            plloutdiv = RCC_PLL_OD_DIV_2;
            pllsysdiv = DISABLE;
            break;
        default:
            return ERROR;
    }

    /* HCLK = SYSCLK */
    RCC_ConfigHclk(RCC_SYSCLK_DIV1);

    /* PCLK2 = HCLK */
    RCC_ConfigPclk2(RCC_HCLK_DIV1);

    /* PCLK1 = HCLK/2 */
    RCC_ConfigPclk1(RCC_HCLK_DIV2);

    /* Configure PLL: source, input prescaler, multiplier, output prescaler */
    RCC_ConfigPll(PLL_src, pllinpre, pllmul, plloutdiv);

    /* Enable PLL */
    RCC_EnablePll(ENABLE);

    /* Wait till PLL is ready */
    while (RCC_GetFlagStatus(RCC_CTRL_FLAG_PLLRDF) != SET)
    {
        if ((timeout_value--) == 0)
        {
            return ERROR;
        }
    }
    
    /* Enable or Disable PLLSYSDIV (SYSCLK = FPLL / pllsysdiv) */
    RCC_EnablePllSysclkDiv(pllsysdiv);

    /* Select PLL as system clock source */
    RCC_ConfigSysclk(RCC_SYSCLK_SRC_PLL);

    /* Wait till PLL is used as system clock source */
    timeout_value = 0xFFFFFFFF;
    while (RCC_GetSysclkSrc() != RCC_SYSCLK_STS_PLL)
    {
        if ((timeout_value--) == 0)
        {
            return ERROR;
        }
    }

    FLASH_SetLatency(latency);
    return SUCCESS;
}


