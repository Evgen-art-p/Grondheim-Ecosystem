//+------------------------------------------------------------------+
//|                                                          iAO.mq4 |
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

#property  indicator_separate_window
#property  indicator_buffers 7
#property  indicator_color2  Lime
#property  indicator_color3  Red
#property  indicator_color4  BlueViolet
#property  indicator_color5  Violet
#property  indicator_color6  Orange
#property  indicator_color7  DodgerBlue

extern bool   alert=true;
extern int    width=1; //размер значка
extern int    BarsToProcess=140; //количество баров для поиска сигнала "два пика"
datetime bar;
bool s1=false,s2=false,s3=false,s4=false;
//---- indicator buffers
double     ExtBuffer0[];
double     ExtBuffer1[];
double     ExtBuffer2[];
double     ExtBuffer3[];
double     ExtBuffer4[];
double     ExtBuffer5[];
double     ExtBuffer6[];

//+------------------------------------------------------------------+
//|         Инициализация пользовательского индикатора               |
//+------------------------------------------------------------------+
int init()
  {
  bar=0;
  s1=false;
  s2=false;
  s3=false;
  s4=false;
   SetIndexStyle(0,DRAW_HISTOGRAM,CLR_NONE);
   SetIndexStyle(1,DRAW_HISTOGRAM);
   SetIndexStyle(2,DRAW_HISTOGRAM);
   SetIndexStyle(3,DRAW_ARROW,0,width);
   SetIndexArrow(3,119);
   SetIndexStyle(4,DRAW_ARROW,0,width);
   SetIndexArrow(4,119);
   SetIndexStyle(5,DRAW_ARROW,0,width);
   SetIndexArrow(5,119);
   SetIndexStyle(6,DRAW_ARROW,0,width);
   SetIndexArrow(6,119);
   
   IndicatorDigits(Digits+1);
   SetIndexDrawBegin(0,34);
   SetIndexDrawBegin(1,34);
   SetIndexDrawBegin(2,34);

   SetIndexBuffer(0,ExtBuffer0);
   SetIndexBuffer(1,ExtBuffer1);
   SetIndexBuffer(2,ExtBuffer2);
   SetIndexBuffer(3,ExtBuffer3);
   SetIndexBuffer(4,ExtBuffer4);
   SetIndexBuffer(5,ExtBuffer5);
   SetIndexBuffer(6,ExtBuffer6);
//---- name for DataWindow and indicator subwindow label
   IndicatorShortName("iAO");
   SetIndexLabel(0,NULL);
   SetIndexLabel(1,NULL);
   SetIndexLabel(2,NULL);
   SetIndexLabel(3,"iAO: блюдце");
   SetIndexLabel(4,"iAO: пересечение нуля");
   SetIndexLabel(5,"iAO: 2-ой мудрец");
   SetIndexLabel(6,"iAO: два пика");
//---- initialization done
   return(0);
  }
//+------------------------------------------------------------------+
//| Awesome Oscillator                                               |
//+------------------------------------------------------------------+
int start()
  {
   int    limit,limit1,limit2;
   int    counted_bars=IndicatorCounted();
   double prev,current;
   double high,high_prev,low,low_prev;
   int    bullcross,bearcross;
   
   if(iBars(Symbol(),Period())<34) 
    {
     Print("Недостаточно баров для расчета индикатора!");
     return(0); 
    }    
//---- Пересчитываем последний бар
   limit = Bars - counted_bars-1;
   if(Bars - counted_bars > 2) limit = Bars-34-1;

   limit1=limit;
   limit2=limit1;
//---- AO
   for(int i=limit; i>=0; i--)
      ExtBuffer0[i]=iAO(Symbol(),Period(),i);
//----Распределения цветов для отображения гистограммы
   for(i=limit1; i>=0; i--)
     {
      if(ExtBuffer0[i]<ExtBuffer0[i+1])
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
      if(bull_dish(i)||bear_dish(i)) 
       {
        ExtBuffer3[i]=ExtBuffer0[i];
        if(i==1)s1=true;
       }
      if(bull_cross(i)||bear_cross(i))
       {
        ExtBuffer4[i]=ExtBuffer0[i];
        if(i==1)s2=true;
       }
      if(bull_second_wisdom(i)||bear_second_wisdom(i))
       {
        ExtBuffer5[i]=ExtBuffer0[i];
        if(i==1)s3=true;
       }
      
      high=GetPeak(i,MODE_UPPER,BarsToProcess);
      high_prev=GetPeak(GetPeak(i,MODE_UPPER,BarsToProcess),MODE_UPPER,BarsToProcess);
      low=GetPeak(i,MODE_LOWER,BarsToProcess);
      low_prev=GetPeak(GetPeak(i,MODE_LOWER,BarsToProcess),MODE_LOWER,BarsToProcess);
      bullcross=Get0CrossShift(i,MODE_UPPER,BarsToProcess);
      bearcross=Get0CrossShift(i,MODE_LOWER,BarsToProcess);
     if(high==i+1||low==i+1)
      {
       if(high_prev<bullcross && high_prev<bearcross && two_high_peaks(i,BarsToProcess))
        {
         ExtBuffer6[i]=ExtBuffer0[i];
         if(i==1)s4=true;
        }
       if(low_prev<bearcross && low_prev<bullcross && two_low_peaks(i,BarsToProcess))
        {
         ExtBuffer6[i]=ExtBuffer0[i];
         if(i==1)s4=true;
        }
      } 
     } 
  if(alert)
    {  
    if(s1 && bar<Time[0])
     {
      Alert("iAC: Сигнал <блюдце> на ",Symbol(),"_",GetNameTF(0),"");
     }
    if(s2 && bar<Time[0])
     {
      Alert("iAC: Сигнал <пересечение нуля> на ",Symbol(),"_",GetNameTF(0),"");
     }
    if(s3 && bar<Time[0])
     {
      Alert("iAC: Сигнал <второй мудрец> на ",Symbol(),"_",GetNameTF(0),"");
     } 
    if(s4 && bar<Time[0])
     {
      Alert("iAC: Сигнал <два пика или основания> на ",Symbol(),"_",GetNameTF(0),"");
     } 
        bar=Time[0]; 
        s1=false;
        s2=false;
        s3=false;
        s4=false;  
    }  
 
    
//---- done
   return(0);
  }
bool bull_dish(int shift)//Бычье блюдце
  {
    if(AO(shift)>AO(shift+1) && AO(shift+2)>AO(shift+1) && AO(shift)>0 && AO(shift+1)>0 && AO(shift+2)>0)
    return(true);else return(false);     
  } 
bool bear_dish(int shift)//Медвежье блюдце
   {
     if(AO(shift)<AO(shift+1) && AO(shift+2)<AO(shift+1) && AO(shift)<0 && AO(shift+1)<0 && AO(shift+2)<0)
     return(true);else return (false);
   }
bool bull_cross(int Shift)//бычье пересечение нулевой линии
   {
     if(AO(Shift+1)<0 && AO(Shift)>0)
     return(true);else return(false);
   }
bool bear_cross(int Shift)//медвежье пересечение нулевой линии
   {
     if(AO(Shift+1)>0 && AO(Shift)<0)
     return(true);else return(false);
   }
//+------------------------------------------------------------------+
//|Возвращает смещение бара на котором свормировался экстремум AO    |
//|mode принимает значения MODE_UPPER и MODE_LOWER                    |                                                                        
//+------------------------------------------------------------------+
int GetPeak(int shift_start, int mode, int BarsToProcess)
 {
   int shift;
   double ao0,ao1,ao2;
   int retn_shift;
    
   for(shift=shift_start;shift<BarsToProcess;shift++)
      {
        ao0=iAO(NULL,0,shift);
        ao1=iAO(NULL,0,shift+1);
        ao2=iAO(NULL,0,shift+2);
          if(mode==MODE_UPPER)
            {
             if(ao0>0 && ao2>0 && ao0<ao1 && ao1>ao2)
              {
                retn_shift=shift;
                break;
              }
            }
          if(mode==MODE_LOWER)
            {
             if(ao0<0 && ao2<0 && ao0>ao1 && ao1<ao2)
              {
                retn_shift=shift;
                break;
              }
            } 
      }
 return(retn_shift+1);
   }
//+------------------------------------------------------------------------+
//|Возвращает смещение бара на котором произошло пересечение нулевой линии |
//|mode принимает значения MODE_UPPER и MODE_LOWER                          |                                                                        
//+------------------------------------------------------------------------+
int Get0CrossShift(int shift_start,int mode,int BarsToProcess) 
   {
    int shift;
     double ao0,ao1;
     int retn_shift=0;
    for(shift=shift_start;shift<BarsToProcess;shift++)
      {
         ao0=iAO(NULL,0,shift);
         ao1=iAO(NULL,0,shift+1);
          if(mode==MODE_UPPER)
           {
            if(ao0>0 && ao1<0)
            {
              retn_shift=shift;
              break;
            }
           }
          if(mode==MODE_LOWER)
           {  
           if(ao0<0 && ao1>0)
            {
              retn_shift=shift;
              break;
            }
           } 
      }
      return(retn_shift+1);
   }

bool two_high_peaks(int Shift,int BarsToProcess)//два пика выше нулевой линии
   {
    int high_peak1=GetPeak(Shift, MODE_UPPER,BarsToProcess);
    int high_peak2=GetPeak(high_peak1,MODE_UPPER,BarsToProcess);
    if(iAO(Symbol(),Period(),high_peak1)<iAO(Symbol(),Period(),high_peak2))
    return(true);else return(false);
   } 
 bool two_low_peaks(int Shift,int BarsToProcess)//два пика ниже нулевой линии
   {
    int low_peak1=GetPeak(Shift,MODE_LOWER,BarsToProcess);
    int low_peak2=GetPeak(low_peak1,MODE_LOWER,BarsToProcess);
    if(iAO(Symbol(),Period(),low_peak1)>iAO(Symbol(),Period(),low_peak2))
    return(true);else return(false);
   }  
   
//+------------------------------------------------------------------+
//|Бычий второй мудрец                                               |
//+------------------------------------------------------------------+   
bool bull_second_wisdom(int shift)
  {
   double ao,ao1,ao2,ao3,ao4;
   ao=iAO(Symbol(),Period(),shift);
   ao1=iAO(Symbol(),Period(),shift+1);
   ao2=iAO(Symbol(),Period(),shift+2);
   ao3=iAO(Symbol(),Period(),shift+3);
   ao4=iAO(Symbol(),Period(),shift+4);
   if(ao>ao1 && ao1>ao2 && ao2>ao3 && ao3<ao4)
    return(true);else return(false);  
  }
//+------------------------------------------------------------------+
//|Медвежий второй мудрец                                            |
//+------------------------------------------------------------------+  
bool bear_second_wisdom(int shift)
  {
   double ao,ao1,ao2,ao3,ao4;
   ao=iAO(Symbol(),Period(),shift);
   ao1=iAO(Symbol(),Period(),shift+1);
   ao2=iAO(Symbol(),Period(),shift+2);
   ao3=iAO(Symbol(),Period(),shift+3);
   ao4=iAO(Symbol(),Period(),shift+4);
   if(ao<ao1 && ao1<ao2 && ao2<ao3 && ao3>ao4)
    return(true);else return(false);  
  }
double AO(int Shift)//функция возвращает значение индикатора AO на баре shift 
   {
     return(NormalizeDouble(iAO(NULL, 0, Shift), Digits + 2));
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
   