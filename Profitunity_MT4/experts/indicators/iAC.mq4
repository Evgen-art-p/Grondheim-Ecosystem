//+------------------------------------------------------------------+
//|                                                           AC.mq4 |
//|                      Copyright © 2010, Dmitry Zhebrak aka Necron |
//|                                                  www.mqlcoder.ru |
//+******************************************************************+
//|Данная версия индикатора предназначена для некомерческого         |
//|использования. Публикация разрешена только при указании имени     |
//|автора ( Necron ). Редактирование исходного разрешается только при|
//|условии сохранения данного текста, ссылок и имени автора. Продажа |
//|индикатора или отдельных его частей ЗАПРЕЩЕНА.                    |
//|Автор не несет ответственности за возможные убытки, полученные в  |
//|результате использования индикатора.                              |
//|По всем вопросам, связанными с работой индикатора или             |
//|или предложениями по его доработке обращаться на email:           |
//|necronfx@gmail.com                                                |
//+******************************************************************+
#property copyright "Copyright © 2010, Dmitry Zhebrak"
#property link      "www.mqlcoder.ru"
#property link      "mailto: necronfx@gmail.com"

#define   version   "1.0.0.0"

//---- indicator settings
#property  indicator_separate_window
#property  indicator_buffers 6
#property  indicator_color1  Black
#property  indicator_color2  Red
#property  indicator_color3  Lime
#property  indicator_color4  Blue
#property  indicator_color5  Violet
#property  indicator_color6  Orange

extern bool   alert=true;
extern int    width=1;//толщина бара гистограммы

//---- indicator buffers
double     ExtBuffer0[];
double     ExtBuffer1[];
double     ExtBuffer2[];
double     ExtBuffer3[];
double     ExtBuffer4[];
double     ExtBuffer5[];

datetime bar;
bool s1=false,s2=false,s3=false;
//+------------------------------------------------------------------+
//| Custom indicator initialization function                         |
//+------------------------------------------------------------------+
int init()
  {
//---- 2 additional buffers are used for counting.
  // IndicatorBuffers(3);
//---- drawing settings
bar=0;
s1=false;
s2=false;
s3=false;
   SetIndexStyle(0,DRAW_HISTOGRAM);
   SetIndexStyle(1,DRAW_HISTOGRAM);
   SetIndexStyle(2,DRAW_HISTOGRAM);
   SetIndexStyle(3,DRAW_ARROW,0,width);
   SetIndexArrow(3,119);
   SetIndexStyle(4,DRAW_ARROW,0,width);
   SetIndexArrow(4,119);
   SetIndexStyle(5,DRAW_ARROW,0,width);
   SetIndexArrow(5,119);
   IndicatorDigits(Digits+2);
   SetIndexDrawBegin(0,38);
   SetIndexBuffer(0,ExtBuffer0);
   SetIndexBuffer(1,ExtBuffer1);
   SetIndexBuffer(2,ExtBuffer2);
   SetIndexBuffer(3,ExtBuffer3);
   SetIndexBuffer(4,ExtBuffer4);
   SetIndexBuffer(5,ExtBuffer5);
   
//---- name for DataWindow and indicator subwindow label
   IndicatorShortName("iAC");
   SetIndexLabel(0,NULL);
   SetIndexLabel(1,NULL);
   SetIndexLabel(2,NULL);
   SetIndexLabel(3,"iAC: 2 бара");
   SetIndexLabel(4,"iAC: 3 бара");
   SetIndexLabel(5,"iAC: пересечение нуля");
//---- initialization done
   return(0);
  }
//+------------------------------------------------------------------+
//| Accelerator/Decelerator Oscillator                               |
//+------------------------------------------------------------------+
int start()
  {
   int    limit,limit2;
   int    counted_bars=IndicatorCounted();
   double prev,current;
   //---- last counted bar will be recounted
  
  if(iBars(Symbol(),Period())<34) 
    {
     Print("Недостаточно баров для расчета индикатора!");
     return(0); 
    }    

   limit = Bars - counted_bars-1;
   if(Bars - counted_bars > 2) limit = Bars-34-1;

   limit2=limit;
   //---- macd counted in the 1-st additional buffer
   for(int i=limit; i>=0; i--)
      ExtBuffer0[i]=iAC(NULL,0,i);
   //---- signal line counted in the 2-nd additional buffer
   //---- dispatch values between 2 buffers
   for(i=limit; i>=0; i--)
     {
      if(ExtBuffer0[i]>ExtBuffer0[i+1])
        {
         ExtBuffer2[i]=ExtBuffer0[i];
         ExtBuffer1[i]=0.0;
        }
      else
        {
         ExtBuffer1[i]=ExtBuffer0[i];
         ExtBuffer2[i]=0.0;
        }
     }
   for(i=limit2;i>=0;i--)
     {
      if(bull_double_bar_above(i)|| bear_double_bar_below(i))
       {
         ExtBuffer3[i]=ExtBuffer0[i];
         if(i==1)s1=true;
       }
      if(bull_triple_bar_below(i)|| bear_triple_bar_above(i)) 
       {
        ExtBuffer4[i]=ExtBuffer0[i];
        if(i==1)s2=true;
       }
      if(bull_cross_and_double_bar(i)|| bear_cross_and_double_bar(i))
       {
        ExtBuffer5[i]=ExtBuffer0[i];
        if(i==1)s3=true;
       }
     } 
   if(alert)
    {  
    if(s1 && bar<Time[0])
     {
      Alert("iAC: Сигнал 2 бара выше/ниже нуля на ",Symbol(),"_",GetNameTF(0),"");
     }
    if(s2 && bar<Time[0])
     {
      Alert("iAC: Сигнал 3 бара выше/ниже нуля на ",Symbol(),"_",GetNameTF(0),"");
     }
    if(s3 && bar<Time[0])
     {
      Alert("iAC: Сигнал 2 бара и пересечение нуля на ",Symbol(),"_",GetNameTF(0),"");
     } 
    bar=Time[0];  
    s1=false;
    s2=false;
    s3=false;
   }  
   //---- done
   return(0);
  }
//+------------------------------------------------------------------+
//---- done

     double AC(int Shift)//функция возвращает значение индикатора AC на баре shift
     {
       return(NormalizeDouble(iAC(NULL, 0, Shift), Digits + 2));
     }

     bool bull_double_bar_above(int Shift)//2 бара выше нулевой линии
     {
      if(AC(Shift)>AC(Shift+1) && AC(Shift+1)>AC(Shift+2) && AC(Shift+2) < AC(Shift+3) && AC(Shift+2) > 0)
      return(true);else return(false);
     }
   bool bull_triple_bar_below(int Shift)//три бара ниже нулевой линии
     {
      if(AC(Shift) > AC(Shift+1) && AC(Shift+1)>AC(Shift+2) && AC(Shift+2)>AC(Shift+3) && AC(Shift+3)<AC(Shift+4) && AC(Shift) < 0 /*) ||(AC(Shift) > 0 && AC(Shift+1) < 0))*/)
      return(true); else return(false);
     }
   bool bull_cross_and_double_bar(int Shift)//два бара ниже нулевой линии и пересечение
     {
      if(AC(Shift)>AC(Shift+1) && AC(Shift+1)>AC(Shift+2) && AC(Shift+2)<AC(Shift+3) && AC(Shift)>0 && AC(Shift+1)<0)
      return(true); else return(false);
     }
   bool bear_double_bar_below(int Shift)//два бара ниже нулевой линии
     { 
      if(AC(Shift)<AC(Shift+1) && AC(Shift+1)<AC(Shift+2) && AC(Shift+2)>AC(Shift+3) && AC(Shift+2)<0)
      return(true); else return(false);
     }
   bool bear_triple_bar_above(int Shift)//три бара выше нулевой линии
     {
      if(AC(Shift)<AC(Shift+1) && AC(Shift+1)<AC(Shift+2) && AC(Shift+2)<AC(Shift+3)&& AC(Shift+3)>AC(Shift+4) && ((AC(Shift)>0) || (AC(Shift)<0 && AC(Shift+2)>0 && AC(Shift+1)<0 )))
      return(true); else return(false);
     }
   bool bear_cross_and_double_bar(int Shift)//два бара выше нулевой линии и пересечение
     {
      if(AC(Shift)<AC(Shift+1) && AC(Shift+1)<AC(Shift+2) && AC(Shift+2)>AC(Shift+3) && AC(Shift)<0 && AC(Shift+1)>0)
      return(true); else return(false);
     }
//+----------------------------------------------------------------------------+
//|  Автор    : Ким Игорь В. aka KimIV,  http://www.kimiv.ru                   |
//+----------------------------------------------------------------------------+
//|  Версия   : 01.09.2005                                                     |
//|  Описание : Возвращает наименование таймфрейма                             |
//+----------------------------------------------------------------------------+
//|  Параметры:                                                                |
//|    TimeFrame - таймфрейм (количество секунд)      (0 - текущий ТФ)         |
//+----------------------------------------------------------------------------+
string GetNameTF(int TimeFrame=0) {
  if (TimeFrame==0) TimeFrame=Period();
  switch (TimeFrame) {
    case PERIOD_M1:  return("M1");
    case PERIOD_M5:  return("M5");
    case PERIOD_M15: return("M15");
    case PERIOD_M30: return("M30");
    case PERIOD_H1:  return("H1");
    case PERIOD_H4:  return("H4");
    case PERIOD_D1:  return("Daily");
    case PERIOD_W1:  return("Weekly");
    case PERIOD_MN1: return("Monthly");
    default:         return("Unknown Period");
  }
}     
     