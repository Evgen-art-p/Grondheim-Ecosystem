//+------------------------------------------------------------------+
//|                                                   iAlligator.mq4 |
//|                       Copyright © 2010, Dmitry Zhebrak aka Necron|
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


#property indicator_chart_window
#property indicator_buffers 4
#property indicator_color1 Blue
#property indicator_color2 Red
#property indicator_color3 Lime
#property indicator_color4 Magenta
//---- input parameters

extern bool Show_Purple=false;
extern int width=1;
extern int JawsPeriod=13;
extern int JawsShift=8;
extern int TeethPeriod=8;
extern int TeethShift=5;
extern int LipsPeriod=5;
extern int LipsShift=3;
extern int PurplePeriod=3;
extern int PurpleShift=1;
//---- indicator buffers
double ExtBlueBuffer[];
double ExtRedBuffer[];
double ExtLimeBuffer[];
double ExtPurpleBuffer[];
//+------------------------------------------------------------------+
//| Custom indicator initialization function                         |
//+------------------------------------------------------------------+
int init()
  {
//---- line shifts when drawing
   SetIndexShift(0,JawsShift);
   SetIndexShift(1,TeethShift);
   SetIndexShift(2,LipsShift);
   SetIndexShift(3,PurpleShift);
//---- first positions skipped when drawing
   SetIndexDrawBegin(0,JawsShift+JawsPeriod);
   SetIndexDrawBegin(1,TeethShift+TeethPeriod);
   SetIndexDrawBegin(2,LipsShift+LipsPeriod);
   SetIndexDrawBegin(3,PurpleShift+PurplePeriod);
//---- 3 indicator buffers mapping
   SetIndexBuffer(0,ExtBlueBuffer);
   SetIndexBuffer(1,ExtRedBuffer);
   SetIndexBuffer(2,ExtLimeBuffer);
   SetIndexBuffer(3,ExtPurpleBuffer);
//---- drawing settings
   SetIndexStyle(0,DRAW_LINE,0,width);
   SetIndexStyle(1,DRAW_LINE,0,width);
   SetIndexStyle(2,DRAW_LINE,0,width);
   SetIndexStyle(3,DRAW_LINE,0,width);
//---- index labels
   SetIndexLabel(0,"Gator Jaws");
   SetIndexLabel(1,"Gator Teeth");
   SetIndexLabel(2,"Gator Lips");
   SetIndexLabel(3,"Gator Purple");
//---- initialization done
   return(0);
  }
//+------------------------------------------------------------------+
//| Bill Williams' Alligator                                         |
//+------------------------------------------------------------------+
int start()
  {
   int limit;
   int counted_bars=IndicatorCounted();
//---- check for possible errors
   if(counted_bars<0) return(-1);
//---- last counted bar will be recounted
   if(counted_bars>0) counted_bars--;
   limit=Bars-counted_bars;
//---- main loop
   for(int i=0; i<limit; i++)
     {     
   ExtBlueBuffer[i]=iMA(NULL,0,JawsPeriod,0,MODE_SMMA,PRICE_MEDIAN,i);
   ExtRedBuffer[i]=iMA(NULL,0,TeethPeriod,0,MODE_SMMA,PRICE_MEDIAN,i);
   ExtLimeBuffer[i]=iMA(NULL,0,LipsPeriod,0,MODE_SMMA,PRICE_MEDIAN,i);
   
   if (Show_Purple)
   ExtPurpleBuffer[i]=iMA(NULL,0,PurplePeriod,0,MODE_SMMA,PRICE_MEDIAN,i);
  }
//---- done
   return(0);
  }
//+------------------------------------------------------------------+

