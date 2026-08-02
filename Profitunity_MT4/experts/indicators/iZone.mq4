//+------------------------------------------------------------------+
//|                                                        iZone.mq4 |
//|                                 Copyright © 2010, Dmitry Zhebrak |
//|                                                www.fxgeneral.com |
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

#property indicator_chart_window
#property indicator_buffers 8
#property indicator_color1 Lime
#property indicator_color2 Lime
#property indicator_color3 Red
#property indicator_color4 Red
#property indicator_color5 Gray
#property indicator_color6 Gray
#property indicator_color7 Lime
#property indicator_color8 Red

extern bool alert=true;
extern bool show_5Bars=true;
extern int width=0;
extern int BarsToProcess=144;
extern color clr_dn=Red;
extern color clr_up=Lime;

extern double mult=1.618;
extern int ATR_Period=34;
//---- buffers
double UpBuffer1[];
double DnBuffer1[];
double UpBuffer2[];
double DnBuffer2[];
double UpBuffer3[];
double DnBuffer3[];

double up[],dn[];
datetime bar;
bool s1,s2;
//+------------------------------------------------------------------+
//| Custom indicator initialization function                         |
//+------------------------------------------------------------------+
int init()
  {
//---- indicators
bar=0;
s1=false;
s2=false;
   SetIndexStyle(0,DRAW_HISTOGRAM);
   SetIndexBuffer(0,UpBuffer1);
   SetIndexStyle(1,DRAW_HISTOGRAM);
   SetIndexBuffer(1,DnBuffer1);
   SetIndexStyle(2,DRAW_HISTOGRAM);
   SetIndexBuffer(2,UpBuffer2);
   SetIndexStyle(3,DRAW_HISTOGRAM);
   SetIndexBuffer(3,DnBuffer2);
   SetIndexStyle(4,DRAW_HISTOGRAM);
   SetIndexBuffer(4,UpBuffer3);
   SetIndexStyle(5,DRAW_HISTOGRAM);
   SetIndexBuffer(5,DnBuffer3);
   SetIndexBuffer(6,up);
   SetIndexStyle(6,DRAW_ARROW);
   SetIndexArrow(6,251);
   SetIndexBuffer(7,dn);
   SetIndexStyle(7,DRAW_ARROW);
   SetIndexArrow(7,251);
   
   SetIndexLabel(0,NULL);
   SetIndexLabel(1,NULL);
   SetIndexLabel(2,NULL);
   SetIndexLabel(3,NULL);
   SetIndexLabel(4,NULL);
   SetIndexLabel(5,NULL);
   SetIndexLabel(6,"5 баров в зеленой зоне");
   SetIndexLabel(7,"5 баров в красной зоне");
   
   return(0);
  }
//+------------------------------------------------------------------+
//| Custom indicator deinitialization function                       |
//+------------------------------------------------------------------+
int deinit()
  {
//----

//----
   return(0);
  }
//+------------------------------------------------------------------+
//| Custom indicator iteration function                              |
//+------------------------------------------------------------------+
int start()
  {
   int    limit,i,limit1;
   int    counted_bars=IndicatorCounted();
   int    pip;
   
   if(iBars(Symbol(),Period())<34) 
    {
     Print("Недостаточно баров для расчета индикатора!");
     return(0); 
    }    

//----
   limit = Bars - counted_bars-1;
   if(Bars - counted_bars > 2) limit = Bars-34-1;
   
//---- initial zero
   if(counted_bars < 1)
      for(i=BarsToProcess;i>=0;i--) 
         {
          UpBuffer1[Bars-i]=0.0;
          UpBuffer2[Bars-i]=0.0;
          UpBuffer3[Bars-i]=0.0;
      
          DnBuffer1[Bars-i]=0.0;
          DnBuffer2[Bars-i]=0.0;
          DnBuffer3[Bars-i]=0.0;
         }
   limit = Bars - counted_bars;
   limit1=limit;
   for(i=limit;i>=0;i--) 
      {	 
       UpBuffer1[i] =EMPTY;
       UpBuffer2[i] =EMPTY; 
       UpBuffer3[i] =EMPTY;
   
       DnBuffer1[i] =EMPTY;
       DnBuffer2[i] =EMPTY;
       DnBuffer3[i] =EMPTY;
       if (AO(i)>AO(i+1) && AC(i)>AC(i+1))
         {
          UpBuffer1[i] = High[i];
          DnBuffer1[i] = Low[i];
         }
       else   
       if (AO(i)<AO(i+1) && AC(i)<AC(i+1))
         {
          UpBuffer2[i] = Low[i];
          DnBuffer2[i] = High[i];
         }
       else   
       if (UpBuffer1[i] == EMPTY && UpBuffer2[i] == EMPTY)  
         {
          UpBuffer3[i] = High[i];
          DnBuffer3[i] = Low[i];
         }
      } 
   if(show_5Bars)
    {   
    for(i=limit1;i>=0;i--)
     {
      double atr=iATR(Symbol(),Period(),ATR_Period,i);
        dn[i]=EMPTY_VALUE;
        up[i]=EMPTY_VALUE;
      if(consbars(MODE_LOWER,i))
       { 
        dn[i]=High[i]+mult*atr/10.0;
        if(i==1)s1=true;
       }
      if(consbars(MODE_UPPER,i)) 
       {
       up[i]=Low[i]-mult*atr/10.0;
       if(i==1)s2=true;
       }


       
     }  
   }
   if(alert)
    {  
    if(s1 && bar<Time[0])
     {
      Alert("iZone: Сигнал <5 баров в красной зоне> на ",Symbol(),"_",GetNameTF(0),"");
     }
    if(s2 && bar<Time[0])
     {
      Alert("iZone: Сигнал <5 баров в зеленой зоне> на ",Symbol(),"_",GetNameTF(0),"");
     }
     bar=Time[0];  
     s1=false;
     s2=false;
    }
//----
   return(0);
  }
//+------------------------------------------------------------------+
bool consbars(int mode,int shift)
 {
  bool result;
  if(mode==MODE_UPPER)
   {
    if(AO(shift)>AO(shift+1) && AO(shift+1)>AO(shift+2) && AO(shift+2)>AO(shift+3) && AO(shift+3)>AO(shift+4) && AO(shift+4)>AO(shift+5) &&
         AC(shift)>AC(shift+1) && AC(shift+1)>AC(shift+2) && AC(shift+2)>AC(shift+3) && AC(shift+3)>AC(shift+4) && AC(shift+4)>AC(shift+5))
         result=true;
   }
  if(mode==MODE_LOWER)
   {
     if(AO(shift)<AO(shift+1) && AO(shift+1)<AO(shift+2) && AO(shift+2)<AO(shift+3) && AO(shift+3)<AO(shift+4) && AO(shift+4)<AO(shift+5) &&
         AC(shift)<AC(shift+1) && AC(shift+1)<AC(shift+2) && AC(shift+2)<AC(shift+3) && AC(shift+3)<AC(shift+4) && AC(shift+4)<AC(shift+5))
         result=true;
   }
  return(result);       
 }
double AO(int Shift)//функция возвращает значение индикатора AO на баре shift 
   {
     return(NormalizeDouble(iAO(NULL, 0, Shift), Digits + 2));
   }
double AC(int Shift)//функция возвращает значение индикатора AC на баре shift
     {
       return(NormalizeDouble(iAC(NULL, 0, Shift), Digits + 2));
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
   