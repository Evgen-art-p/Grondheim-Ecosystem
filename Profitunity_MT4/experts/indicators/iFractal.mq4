//+------------------------------------------------------------------+
//|                                                           AC.mq4 |
//|                      Copyright © 2010, Dmitry Zhebrak aka Necron |
//|                                                www.fxgeneral.com |
//+------------------------------------------------------------------+
//|                                                       Lizhniyk E |
//|                                        http://www.metaquotes.net |
//+------------------------------------------------------------------+
/*
Добавлены к коду Lizhniyk-а след.функции:
-отображение уровней последних фракталов вверх и вниз
-отображение ценовых меток на них
-алерт при пробое фрактала вверх или вниз
-немного изменен алгоритм рассчета расстояния от экстремума бара к значку фрактала
*/
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
#property indicator_width1 1
#property indicator_width2 1
#property indicator_color1 Lime
#property indicator_color2 Red
//---- input parameters
extern bool alert=false;
extern int    Size = 1; 
extern int    range_fractal=5;
extern double multiplier=2;
extern bool   show_level=false;
extern color  fr_up_color=Lime;
extern color  fr_dn_color=Red;
extern int    width=1;
extern int    style=0;
int    Bars_ATR=233;//период для ATR                                                          
int    Code_Arrow_UP=217;                                                                     
int    Code_Arrow_DN=218; 

//---- buffers
double Ext1[];
double Ext2[];
int center=0;
datetime bar;
//+------------------------------------------------------------------+
//| Custom indicator initialization function                         |
//+------------------------------------------------------------------+
int init()
  {
//---- indicators
   if(range_fractal % 2 == 0) range_fractal++;
   if(range_fractal<3) range_fractal=3;
   center=range_fractal/2 + 1 ;
   //scenter=range_fractal/2;
   SetIndexStyle(0,DRAW_ARROW,EMPTY,Size);
   SetIndexArrow(0,Code_Arrow_UP);
   SetIndexBuffer(0,Ext1);
   SetIndexEmptyValue(0,0.0);
   SetIndexStyle(1,DRAW_ARROW,EMPTY,Size);
   SetIndexArrow(1,Code_Arrow_DN);
   SetIndexBuffer(1,Ext2);
   SetIndexEmptyValue(1,0.0);
   SetIndexLabel(0,"Фрактал вверх");
   SetIndexLabel(1,"Фрактал вниз");
   bar=0;
//----
   return(0);
  }
//+------------------------------------------------------------------+
//| Custom indicator deinitialization function                       |
//+------------------------------------------------------------------+
int deinit()
  {
//----
      ObjectDelete("fr_up");
      ObjectDelete("fr_dn");
      ObjectDelete("fr_dn_price");
      ObjectDelete("fr_up_price");

//----
   return(0);
  }
//+------------------------------------------------------------------+
//| Custom indicator iteration function                              |
//+------------------------------------------------------------------+
double cur=0;
double range;
bool found=false;
double fr_up,fr_dn;
  bool   AlertUP, AlertDOWN;

int start()
  {
   int    counted_bars=IndicatorCounted();
   range=iATR(NULL,0,Bars_ATR,0);
//----
   for(int i=Bars-counted_bars;i>=0;i--)
    {
    //*************fractal_up**************
    found=false;
    cur=High[i+center];
    if(cur>=High[i+1] && cur>=High[i+range_fractal])
     {
       found=true;
       AlertUP = true;
     }
    else found=false; 
    if(found) 
     {
     for(int j=1;j<center;j++)
       {
       if(cur>High[i+center-j] && cur>=High[i+center+j]) found=true;
       else {found=false; break;}
       }  
      } 
    if(found) 
    {
      Ext1[i+center]=cur+range*multiplier/10; Ext1[i+center+1]=0;
      fr_up=cur;
      if(show_level)
       {
        ObjectCreate("fr_up",OBJ_TREND,0,0,0,0,0); 
        ObjectSet("fr_up",OBJPROP_TIME1,iTime(Symbol(),Period(),i+center));
		  ObjectSet("fr_up",OBJPROP_TIME2,iTime(Symbol(),Period(),0));
 		  ObjectSet("fr_up",OBJPROP_PRICE1,cur);
 		  ObjectSet("fr_up",OBJPROP_PRICE2,cur);
  		  ObjectSet("fr_up",OBJPROP_RAY,false);
  		  ObjectSet("fr_up",OBJPROP_WIDTH,width); 
		  ObjectSet("fr_up",OBJPROP_COLOR,fr_up_color); 
 		  ObjectSet("fr_up",OBJPROP_STYLE,style); 
        create_label("fr_up_price",cur,fr_up_color);
       }
    }
    
    //*************fractal down************* 
    found=false;
    cur=Low[i+center]; 
    if(cur<=Low[i+1] && cur<=Low[i+range_fractal]) found=true;
    else found=false; 
    if(found) 
     {
     for(int k=1;k<center;k++)
       {
       if(cur<Low[i+center-k] && cur<=Low[i+center+k])
        {
         found=true;
         AlertDOWN = true;
        }
       else {found=false; break;}
       }  
      } 
    if(found) 
    {
     Ext2[i+center]=cur-range*multiplier/10; Ext2[i+center+1]=0;
     fr_dn=cur;
     if(show_level)
       {
        ObjectCreate("fr_dn",OBJ_TREND,0,0,0,0,0); 
        ObjectSet("fr_dn",OBJPROP_TIME1,iTime(Symbol(),Period(),i+center));
		  ObjectSet("fr_dn",OBJPROP_TIME2,iTime(Symbol(),Period(),0));
 		  ObjectSet("fr_dn",OBJPROP_PRICE1,cur);
 		  ObjectSet("fr_dn",OBJPROP_PRICE2,cur);
  		  ObjectSet("fr_dn",OBJPROP_RAY,false);
  		  ObjectSet("fr_dn",OBJPROP_WIDTH,width); 
		  ObjectSet("fr_dn",OBJPROP_COLOR,fr_dn_color);
 		  ObjectSet("fr_dn",OBJPROP_STYLE,style); 
        
        create_label("fr_dn_price",cur,fr_dn_color);
       }
    }
 }
//Print("fr_up=",fr_up," fr_dn=",fr_dn,"");
if (alert == true && Low[0]<=fr_up && High[0]>=fr_up && bar<Time[0]) 
 {
  Alert ("Пробой фрактала вверх на ",Symbol(),"_",GetNameTF(0),"");
 }
if (alert == true && High[0]>=fr_dn && Low[0]<=fr_dn && bar<Time[0])
 {
  Alert ("Пробой фрактала вниз на ",Symbol(),"_",GetNameTF(0),"");
 }
  bar=Time[0];
//----
   return(0);
  }
//+------------------------------------------------------------------+

void create_label(string name,double price,color _color)
 {
 datetime time;
 time=iTime(Symbol(),Period(),0);
     if(ObjectFind(name)!=-1) ObjectMove(name,0,time,price);

  ObjectCreate(name,OBJ_ARROW,0,time,price,time,price);
  ObjectSet(name,OBJPROP_ARROWCODE,6);
  ObjectSet(name,OBJPROP_WIDTH,width);
  ObjectSet(name,OBJPROP_COLOR,_color);

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
 