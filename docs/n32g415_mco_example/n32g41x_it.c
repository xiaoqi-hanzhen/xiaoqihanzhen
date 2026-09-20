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
*\*\file      n32g41x_it.c
*\*\author    Nsing
*\*\version   v1.0.0
*\*\copyright Copyright (c) 2025, Nsing Technologies Inc. All rights reserved. 
**/
#include "n32g41x_it.h"

/**
*\*\name    NMI_Handler.
*\*\fun     Non-Maskable Interrupt handler.
*\*\param   none
*\*\return  none
**/

/** Cortex-M Processor Exceptions Handlers **/
/**
 *\*\name   NMI_Handler.
 *\*\fun    This function handles NMI exception.
 *\*\param  none
 *\*\return none
 */
void NMI_Handler(void)
{
}

/**
 *\*\name   HardFault_Handler.
 *\*\fun    This function handles Hard Fault exception.
 *\*\param  none
 *\*\return none
 */
void HardFault_Handler(void)
{
    /* Go to infinite loop when Hard Fault exception occurs */
    while (1)
    {
    }
}

/**
 *\*\name   MemManage_Handler.
 *\*\fun    This function handles Memory Manage exception.
 *\*\param  none
 *\*\return none
 */
void MemManage_Handler(void)
{
    /* Go to infinite loop when Memory Manage exception occurs */
    while (1)
    {
    }
}

/**
 *\*\name   BusFault_Handler.
 *\*\fun    This function handles Bus Fault exception.
 *\*\param  none
 *\*\return none
 */
void BusFault_Handler(void)
{
    /* Go to infinite loop when Bus Fault exception occurs */
    while (1)
    {
    }
}

/**
 *\*\name   UsageFault_Handler.
 *\*\fun    This function handles Usage Fault exception.
 *\*\param  none
 *\*\return none
 */
void UsageFault_Handler(void)
{
    /* Go to infinite loop when Usage Fault exception occurs */
    while (1)
    {
    }
}

/**
 *\*\name   SVC_Handler.
 *\*\fun    This function handles SVCall exception.
 *\*\param  none
 *\*\return none
 */
void SVC_Handler(void)
{
}

/**
 *\*\name   DebugMon_Handler.
 *\*\fun    This function handles Debug Monitor exception.
 *\*\param  none
 *\*\return none
 */
void DebugMon_Handler(void)
{
}

/**
*\*\name    PendSV_Handler.
*\*\fun     This function handles PendSV_Handler exception.
*\*\param   none
*\*\return  none
**/
void PendSV_Handler(void)
{
}

/**
*\*\name    SysTick_Handler.
*\*\fun     This function handles SysTick Handler.
*\*\param   none
*\*\return  none 
**/
void SysTick_Handler(void)
{
}


/* n32g41x Peripherals Interrupt Handlers, interrupt handler's name please refer to the startup file (startup_n32g41x.s). */


