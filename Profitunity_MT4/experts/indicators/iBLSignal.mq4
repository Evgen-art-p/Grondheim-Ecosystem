//+------------------------------------------------------------------+
//|                                                    iBLSignal.mq4 |
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
#property indicator_buffers 2
#property indicator_color1 Red
#property indicator_color2 Lime

extern int width=0;
double   dn[],
         up[]; 
//+------------------------------------------------------------------+
//| Custom indicator initialization function                         |
//+------------------------------------------------------------------+
int init()
  {
  SetIndexBuffer(0,dn);
  SetIndexBuffer(1,up);
  
  SetIndexStyle(0,DRAW_ARROW,0,width);
  SetIndexStyle(1,DRAW_ARROW,0,width);
  
  SetIndexArrow(0,159);
  SetIndexArrow(1,159);
  
  SetIndexLabel(0,"Продажа Линии Баланса");
  SetIndexLabel(1,"Покупка Линии Баланса");
//---- indicators
//----
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
   int   limit,counted_bars=IndicatorCounted();
   double jaw,atr;
   limit = Bars - counted_bars-1;
   if(Bars - counted_bars > 2) limit = Bars-34-1;
   
   for(int i=limit; i>=0; i--)
    {
     jaw=iAlligator(Symbol(),Period(),13,8,8,5,5,3,MODE_SMMA,PRICE_MEDIAN,MODE_GATORJAW,i+1);
     
     if(Low[i]>Low[i+1])
      {
       if(Low[i+1]<jaw)
        {
         if(Zone(i)==1)
          {
           dn[i]=Low[GetSecond(i+1,MODE_LOWER)];
          }
         else dn[i]=Low[i+1];
        }
       else if(Low[i+1]>jaw)
        {
         if(Zone(i)==1)
          {
           dn[i]=Low[GetSecond(GetSecond(GetSecond(i+1,MODE_LOWER),MODE_LOWER),MODE_LOWER)];
          }
         else dn[i]=Low[GetSecond(i+1,MODE_LOWER)];
        }
      }  
     if(High[i]<High[i+1])
      {
       if(High[i+1]>jaw)
        {
         if(Zone(i)==-1)
          {
           up[i]=High[GetSecond(i+1,MODE_UPPER)];
          }
         else up[i]=High[i+1];
        }  
       else if(High[i+1]<jaw)
        {
         if(Zone(i)==-1)
          {
           up[i]=High[GetSecond(GetSecond(GetSecond(i+1,MODE_UPPER),MODE_UPPER),MODE_UPPER)];   
          }
         else up[i]=High[GetSecond(i+1,MODE_UPPER)];        
        }  
      }  
   }
//----
   
//----
   return(0);
  }
//+------------------------------------------------------------------+
int GetSecond(int shift,int mode)
 {
  int res=0;
  double high,high1,low,low1;
   for(int j=shift;j<Bars-1;j++)
    {
     if(mode==MODE_UPPER)
      {
       if(High[j]>High[shift])
        {
         res=j;
         break;
        }
      }
     else if(mode==MODE_LOWER)
      {
       if(Low[j]<Low[shift])
        {
         res=j;
         break;
        }
      } 
    }
   return(res);
 } 
double AO(int Shift)//функция возвращает значение индикатора AO на баре shift 
   {
     return(NormalizeDouble(iAO(NULL, 0, Shift), Digits + 2));
   }
double AC(int Shift)//функция возвращает значение индикатора AC на баре shift
     {
       return(NormalizeDouble(iAC(NULL, 0, Shift), Digits + 2));
     }
int Zone(int shift)
 {
  int res;
  if     (AO(shift)>AO(shift+1) && AC(shift)>AC(shift+1)) res=1;
  else if(AO(shift)<AO(shift+1) && AC(shift)<AC(shift+1)) res=-1;
  
  return(res);
 } 

