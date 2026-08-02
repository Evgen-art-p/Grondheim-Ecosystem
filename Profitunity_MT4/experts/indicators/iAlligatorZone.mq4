//+------------------------------------------------------------------+
//|                                               iAlligatorZone.mq4 |
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

#property indicator_separate_window    
#property  indicator_buffers 5         
#property  indicator_color1  Black     
#property  indicator_color2  Lime     
#property  indicator_color3  Red
#property  indicator_color4  Lime  
#property  indicator_color5  Red        

//---- indicator parameters 
extern bool    alert=true; // 
extern bool    write_file=true;
string         file_name="FXG_iAlligatorZone";
int            History    =3000;           

double     ExtBuffer0[];                
double     ExtBuffer1[];
double     ExtBuffer2[];
double     ExtBuffer3[];
double     ExtBuffer4[];
datetime bar;

//+------------------------------------------------------------------+ 
//| Custom indicator initialization function                         | 
//+------------------------------------------------------------------+ 
int init() 
  { 
  bar=0;
   SetIndexStyle(0,DRAW_HISTOGRAM);
   SetIndexStyle(1,DRAW_HISTOGRAM);
   SetIndexStyle(2,DRAW_HISTOGRAM);
   SetIndexStyle(3,DRAW_HISTOGRAM,EMPTY,2);
   SetIndexStyle(4,DRAW_HISTOGRAM,EMPTY,2);

   SetIndexBuffer(0,ExtBuffer0);
   SetIndexBuffer(1,ExtBuffer1);
   SetIndexBuffer(2,ExtBuffer2);
   SetIndexBuffer(3,ExtBuffer3);
   SetIndexBuffer(4,ExtBuffer4);

   IndicatorShortName("Al_Zone");
   
   SetIndexLabel(0,NULL);
   SetIndexLabel(1,NULL);
   SetIndexLabel(2,NULL);
   SetIndexLabel(3,NULL);
   SetIndexLabel(4,NULL);
//---- initialization done
   return(0);
  } 
//+------------------------------------------------------------------+ 
//| Custor indicator deinitialization function                       | 
//+------------------------------------------------------------------+ 
int deinit() 
  { 
//---- TODO: add your code here 


//---- 
   return(0); 
  } 
int start()                         // Специальная функция start()
  {
   double jaw,teeth,lips,EMA4,close;                 
   int i,n,Counted_bars;
   string text;

   Counted_bars=IndicatorCounted(); // Количество просчитанных баров 
   i=Bars-Counted_bars-1;           // Индекс первого непосчитанного
   if (i>History-1)                 // Если много баров то ..
      i=History-1;                  // ..рассчитывать заданное колич.
      ExtBuffer1[i] = 0;            // обнуление значений массивов линий индикатора
      ExtBuffer2[i] = 0;
      ExtBuffer0[i] = 0;
      ExtBuffer3[i] = 0;
      ExtBuffer4[i] = 0;
      
   while(i>=0)                      // Цикл по непосчитанным барам
     {       
      jaw=iAlligator(Symbol(),Period(),13,8,8,5,5,3,MODE_SMMA,PRICE_MEDIAN,MODE_GATORJAW,i); // 
      teeth=iAlligator(Symbol(),Period(),13,8,8,5,5,3,MODE_SMMA,PRICE_MEDIAN,MODE_GATORTEETH,i); 
      lips=iAlligator(Symbol(),Period(),13,8,8,5,5,3,MODE_SMMA,PRICE_MEDIAN,MODE_GATORLIPS,i); 
      EMA4=iMA(NULL,0,3,1,MODE_SMMA,PRICE_MEDIAN,i); //
      close=iClose(NULL,0,i);
      ExtBuffer1[i] = 0;
      ExtBuffer2[i] = 0;
      ExtBuffer0[i] = 0; 
      ExtBuffer3[i] = 0; 
      ExtBuffer4[i] = 0; 
     
      if (close>jaw && close>teeth && close>lips)ExtBuffer1[i]=1; 
      if (close<jaw && close<teeth && close<lips)ExtBuffer2[i]=1;
      if (close>jaw && close>teeth && close>lips && close>EMA4)ExtBuffer3[i]=1;
      if (close<jaw && close<teeth && close<lips && close<EMA4)ExtBuffer4[i]=1;
      else ExtBuffer0[i] = 1;    
      
       
      
    if(i==1)  
     {
      if(write_file)
       {
        if(close>jaw && close>teeth && close>lips && lips>=teeth  && bar<Time[0])
         {
          text=TimeToStr(TimeCurrent(), TIME_DATE|TIME_SECONDS)+"; Сильный тренд вверх на "+Symbol()+"_"+GetNameTF(Period())+"";

          WritingLineInFile(file_name+" "+TimeToStr(TimeCurrent(), TIME_DATE)+".txt",text);
         } 
        if(close<jaw && close<teeth && close<lips && lips<=teeth && bar<Time[0])
         {
          text=TimeToStr(TimeCurrent(), TIME_DATE|TIME_SECONDS)+"; Сильный тренд вниз на "+Symbol()+"_"+GetNameTF(Period())+"";
          WritingLineInFile(file_name+" "+TimeToStr(TimeCurrent(), TIME_DATE)+".txt",text);
         } 
       }
      if(alert)
       {
        if(close>jaw && close>teeth && close>lips && lips>=teeth && bar<Time[0])
         {
          Alert ("iAlligator_Zone: Сильный тренд вверх на "+Symbol()+"_"+GetNameTF(Period())+"");
          bar=Time[0];
         }
        if(close<jaw && close<teeth && close<lips && lips<=teeth  && bar<Time[0])   
         {
         Alert ("iAlligator_Zone: Сильный тренд вниз на "+Symbol()+"_"+GetNameTF(Period())+"");
         bar=Time[0];
         }
       }
     }   
      i--;                          // Расчёт индекса следующего бара
     }
   return;                          // Выход из спец. ф-ии start()
  }

//+----------------------------------------------------------------------------+
//|  Автор    : Ким Игорь В. aka KimIV,  http://www.kimiv.ru                   |
//+----------------------------------------------------------------------------+
//|  Версия   : 01.09.2005                                                     |
//+----------------------------------------------------------------------------+
//|  Описание : Запись строки в файл                                           |
//|  Параметры:                                                                |
//|    FileName - имя файла                                                    |
//|    text     - строка                                                       |
//+----------------------------------------------------------------------------+
void WritingLineInFile(string FileName, string text) {
  int file_handle=FileOpen(FileName, FILE_READ|FILE_WRITE, " ");

  if (file_handle>0) {
    FileSeek (file_handle, 0, SEEK_END);
    FileWrite(file_handle, text);
    FileClose(file_handle);
  }
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