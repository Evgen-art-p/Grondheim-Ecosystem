//+******************************************************************+
//|                                               iDivergenceBar.mq4 |
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
#property indicator_chart_window
#property indicator_buffers 4
#property indicator_color1 Red
#property indicator_color2 Red
#property indicator_color3 Lime
#property indicator_color4 Lime


extern int width=2;
extern int ATR=1;

//---- buffers
double UpBuffer1[];
double DnBuffer1[];
double UpBuffer2[];
double DnBuffer2[];
int    BarsCount;
int    Length = 144;
int    limit;
//+------------------------------------------------------------------+
//| Custom indicator initialization function                         |
//+------------------------------------------------------------------+
int init()
  {
//---- indicators
   SetIndexStyle(0,DRAW_HISTOGRAM,0,width);
   SetIndexBuffer(0,UpBuffer1);
   SetIndexStyle(1,DRAW_HISTOGRAM,0,width);
   SetIndexBuffer(1,DnBuffer1);
   SetIndexStyle(2,DRAW_HISTOGRAM,0,width);
   SetIndexBuffer(2,UpBuffer2);
   SetIndexStyle(3,DRAW_HISTOGRAM,0,width);
   SetIndexBuffer(3,DnBuffer2);
//----
   SetIndexLabel(0,NULL);
   SetIndexLabel(1,NULL);
   SetIndexLabel(2,NULL);
   SetIndexLabel(3,NULL);
   SetIndexLabel(4,NULL);
   SetIndexLabel(5,NULL);//----
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
   int  i, BarsCount = IndicatorCounted();
   double atr,lips,teeth,jaw,up,dn;
//----
   if(Bars<=Length) return(0);
   atr=iATR(NULL,0,ATR,i);
//---- initial zero
   if(BarsCount < 1)
      for(i=1;i<=Length;i++) 
         {
          UpBuffer1[Bars-i]=0.0;
          UpBuffer2[Bars-i]=0.0;
      
          DnBuffer1[Bars-i]=0.0;
          DnBuffer2[Bars-i]=0.0;
         }
   if ( BarsCount >  0 )  limit = Bars - BarsCount;
   if ( BarsCount == 0 )  limit = Bars - Length - 1; 
        
   for(i=limit;i>=0;i--) 
      {	 
       UpBuffer1[i] =EMPTY;
       UpBuffer2[i] =EMPTY; 
   
       DnBuffer1[i] =EMPTY;
       DnBuffer2[i] =EMPTY;
       
       lips=iAlligator(Symbol(),Period(),13,8,8,5,5,3,MODE_SMMA,PRICE_MEDIAN,MODE_GATORLIPS,i);
       teeth=iAlligator(Symbol(),Period(),13,8,8,5,5,3,MODE_SMMA,PRICE_MEDIAN,MODE_GATORTEETH,i);
       jaw=iAlligator(Symbol(),Period(),13,8,8,5,5,3,MODE_SMMA,PRICE_MEDIAN,MODE_GATORJAW,i);
       
       up=MathMax(lips,MathMax(teeth,jaw));
       dn=MathMin(lips,MathMin(teeth,jaw));
       
       if (/*Close[i+1]>Open[i+1]*/  High[i]>High[i+1] && Close[i]<High[i]-0.5*(High[i]-Low[i]) && Low[i]>up)
         {
          UpBuffer1[i] = Low[i]+(High[i]-Low[i])/2+(High[i]-Low[i])/10;
          DnBuffer1[i] = Low[i]+(High[i]-Low[i])/2-(High[i]-Low[i])/10;
         }
       else   
       if (/*Close[i+1]<Open[i+1]*/ Low[i]<Low[i+1] && Close[i]>Low[i]+0.5*(High[i]-Low[i]) && High[i]<dn)
         {
          UpBuffer2[i] = Low[i]+(High[i]-Low[i])/2+(High[i]-Low[i])/10;
          DnBuffer2[i] = Low[i]+(High[i]-Low[i])/2-(High[i]-Low[i])/10;
         }
      } 
//----
   return(0);
  }
//+------------------------------------------------------------------+