//+------------------------------------------------------------------+
//|                                          sFractal_StopOrders.mq4 |
//|                      Copyright © 2010, Dmitry Zhebrak aka Necron |
//|                                                  www.mqlcoder.ru |
//+------------------------------------------------------------------+
#property copyright "Copyright © 2010, Dmitry Zhebrak"
#property link      "www.mqlcoder.ru"
#property link      "mailto: necronfx@gmail.com"

#define   version   "1.0.0.0"

#property show_inputs
extern bool       buy=true;
extern bool       MarketWatch=false;
extern double     lot=0.1;
extern string     comment="Fr++";
extern int        MagicNumber=20100529;

extern int        NumberOfTry=10;
extern int        Slippage=2;
extern string     ModeSetOrders_note="1-Корректировка ценовых уровней,2-Вход по текущим ценам";
extern int        modeSetOrders=1;// 1-Корректировка ценовых уровней,2-Вход по текущим ценам
extern bool       UseSound=true;
extern string     SoundSuccess="ok.wav";
extern string     SoundError="wait.wav";
bool gbDisabled=false;

bool AllMessages, PrintEnable;

#include <stdlib.mqh>
//+------------------------------------------------------------------+
//| script program start function                                    |
//+------------------------------------------------------------------+
int start()
  {
  double fr_dn=NormalizeDouble(FindNearFractal(NULL,0,MODE_LOWER),Digits);
  double fr_up=NormalizeDouble(FindNearFractal(NULL,0,MODE_UPPER),Digits);
  double spread=MarketInfo(Symbol(),MODE_SPREAD)*Point;
  int tb,ts;
           if(buy==true)
            {
             SetOrder(Symbol(),OP_BUYSTOP,lot,fr_up+spread,NormalizeDouble(FindNearFractal(NULL,0,MODE_LOWER),Digits),0,MagicNumber,""+comment+"",0); 
            }
         else
            {
             SetOrder(Symbol(),OP_SELLSTOP,lot,fr_dn-spread,NormalizeDouble(FindNearFractal(NULL,0,MODE_UPPER),Digits),0,MagicNumber,""+comment+"",0); 
            }
         return(0);
//----
   return(0);
  }
//+------------------------------------------------------------------+
//+----------------------------------------------------------------------------+
//|  Автор    : Ким Игорь В. aka KimIV,  http://www.kimiv.ru                   |
//+----------------------------------------------------------------------------+
//|  Версия   : 02.08.2008                                                     |
//|  Описание : Установка ордера.                                              |
//+----------------------------------------------------------------------------+
//|  Параметры:                                                                |
//|    sy - наименование инструмента   (NULL или "" - текущий символ)          |
//|    op - операция                                                           |
//|    ll - лот                                                                |
//|    pp - цена                                                               |
//|    sl - уровень стоп                                                       |
//|    tp - уровень тейк                                                       |
//|    mn - Magic Number                                                       |
//|    co - комментарий                                                        |
//|    ex - Срок истечения                                                     |
//+----------------------------------------------------------------------------+
void SetOrder(string sy, int op, double ll, double pp,
              double sl=0, double tp=0, int mn=0, string co="", datetime ex=0) {                                     
  color    clOpen;
  datetime ot;
  double   pa, pb, mp;
  int      err, it, ticket, msl;

  if (sy=="" || sy=="0") sy=Symbol();
  msl=MarketInfo(sy, MODE_STOPLEVEL);
  if (co=="") co=WindowExpertName()+" "+GetNameTF(Period());
  if (ex>0 && ex<TimeCurrent()) ex=0;
  for (it=1; it<=NumberOfTry; it++) {
      if (!IsTesting() && (!IsExpertEnabled() || IsStopped())) {
      Print("SetOrder(): Остановка работы функции");
      Alert("Отжата кнопка <советники>");
      break;
    }
    while (!IsTradeAllowed()) Sleep(5000);
    RefreshRates();
    ot=TimeCurrent();
    ticket=OrderSend(sy, op, ll, pp, Slippage, sl, tp, co, mn, ex, CLR_NONE);
    if (ticket>0) {
      if (UseSound) PlaySound(SoundSuccess); break;
    } else {
      err=GetLastError();
      if (err==128 || err==142 || err==143) {
        Sleep(1000*66);
        if (ExistOrders(sy, op, mn, ot)) {
          if (UseSound) PlaySound(SoundSuccess); break;
        }
        Print("Error(",err,") set order: ",ErrorDescription(err),", try ",it);
        continue;
      }
      if (UseSound) PlaySound(SoundError);
      mp=MarketInfo(sy, MODE_POINT);
      pa=MarketInfo(sy, MODE_ASK);
      pb=MarketInfo(sy, MODE_BID);
      if (pa==0 && pb==0) Message("SetOrder(): Проверьте в обзоре рынка наличие символа "+sy);
      Print("Error(",err,") set order: ",ErrorDescription(err),", try ",it);
      Print("Ask=",pa,"  Bid=",pb,"  sy=",sy,"  ll=",ll,"  op=",GetNameOP(op),
            "  pp=",pp,"  sl=",sl,"  tp=",tp,"  mn=",mn);
      // Неправильные стопы
      if (err==130) {
        // Корректировка ценовых уровней
        if (modeSetOrders==1) {
          Sleep(1000*5.3);
          switch (op) {
            case OP_BUYLIMIT:
              if (pp>pa-msl*mp) pp=pa-msl*mp;
              if (sl>pp-(msl+1)*mp) sl=pp-(msl+1)*mp;
              if (tp>0 && tp<pp+(msl+1)*mp) tp=pp+(msl+1)*mp;
              break;
            case OP_BUYSTOP:
              if (pp<pa+(msl+1)*mp) pp=pa+(msl+1)*mp;
              if (sl>pp-(msl+1)*mp) sl=pp-(msl+1)*mp;
              if (tp>0 && tp<pp+(msl+1)*mp) tp=pp+(msl+1)*mp;
              break;
            case OP_SELLLIMIT:
              if (pp<pb+msl*mp) pp=pb+msl*mp;
              if (sl>0 && sl<pp+(msl+1)*mp) sl=pp+(msl+1)*mp;
              if (tp>pp-(msl+1)*mp) tp=pp-(msl+1)*mp;
              break;
            case OP_SELLSTOP:
              if (pp>pb-msl*mp) pp=pb-msl*mp;
              if (sl>0 && sl<pp+(msl+1)*mp) sl=pp+(msl+1)*mp;
              if (tp>pp-(msl+1)*mp) tp=pp-(msl+1)*mp;
              break;
          }
          Print("SetOrder(): Скорректированы ценовые уровни");
          continue;
        }
        // Вход по текущим ценам
        if (modeSetOrders==2) {
          Print("SetOrder(): Вход по текущим ценам");
          if (op==OP_BUYLIMIT || op==OP_BUYSTOP) OpenPosition(sy, OP_BUY, ll, sl, tp, mn, co);
          if (op==OP_SELLLIMIT || op==OP_SELLSTOP) OpenPosition(sy, OP_SELL, ll, sl, tp, mn, co);
          break;
        }
      }
      // Блокировка работы советника
      if (err==2 || err==64 || err==65 || err==133) {
        gbDisabled=True; break;
      }
      // Длительная пауза
      if (err==4 || err==131 || err==132) {
        Sleep(1000*300); break;
      }
      // Слишком частые запросы (8) или слишком много запросов (141)
      if (err==8 || err==141) Sleep(1000*100);
      if (err==139 || err==140 || err==148) break;
      // Ожидание освобождения подсистемы торговли
      if (err==146) while (IsTradeContextBusy()) Sleep(1000*11);
      // Обнуление даты истечения
      if (err==147) {
        ex=0; continue;
      }
      if (err!=135 && err!=138) Sleep(1000*7.7);
    }
  }
}

//+----------------------------------------------------------------------------+
//|  Возвращает наименование торговой операции                                 |
//|  Параметры:                                                                |
//|    op - идентификатор торговой операции                                    |
//+----------------------------------------------------------------------------+
string GetNameOP(int op) {
	switch (op) {
		case OP_BUY      : return("Buy");
		case OP_SELL     : return("Sell");
		case OP_BUYLIMIT : return("Buy Limit");
		case OP_SELLLIMIT: return("Sell Limit");
		case OP_BUYSTOP  : return("Buy Stop");
		case OP_SELLSTOP : return("Sell Stop");
		default          : return("Unknown Operation");
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
//+----------------------------------------------------------------------------+
//|  Автор    : Ким Игорь В. aka KimIV,  http://www.kimiv.ru                   |
//+----------------------------------------------------------------------------+
//|  Версия   : 12.03.2008                                                     |
//|  Описание : Возвращает флаг существования ордеров.                         |
//+----------------------------------------------------------------------------+
//|  Параметры:                                                                |
//|    sy - наименование инструмента   (""   - любой символ,                   |
//|                                     NULL - текущий символ)                 |
//|    op - операция                   (-1   - любой ордер)                    |
//|    mn - MagicNumber                (-1   - любой магик)                    |
//|    ot - время открытия             ( 0   - любое время установки)          |
//+----------------------------------------------------------------------------+
bool ExistOrders(string sy="", int op=-1, int mn=-1, datetime ot=0) {
  int i, k=OrdersTotal(), ty;

  if (sy=="0") sy=Symbol();
  for (i=0; i<k; i++) {
    if (OrderSelect(i, SELECT_BY_POS, MODE_TRADES)) {
      ty=OrderType();
      if (ty>1 && ty<6) {
        if ((OrderSymbol()==sy || sy=="") && (op<0 || ty==op)) {
          if (mn<0 || OrderMagicNumber()==mn) {
            if (ot<=OrderOpenTime()) return(True);
          }
        }
      }
    }
  }
  return(False);
}
//+----------------------------------------------------------------------------+
//|  Автор    : Ким Игорь В. aka KimIV,  http://www.kimiv.ru                   |
//+----------------------------------------------------------------------------+
//|  Версия   : 01.09.2005                                                     |
//|  Описание : Вывод сообщения в коммент и в журнал                           |
//+----------------------------------------------------------------------------+
//|  Параметры:                                                                |
//|    m - текст сообщения                                                     |
//+----------------------------------------------------------------------------+
void Message(string m) {
  static string prevMessage="";
  Comment(m);
  if (StringLen(m)>0 && PrintEnable) {
    if (AllMessages || prevMessage!=m) {
      prevMessage=m;
      Print(m);
    }
  }
}
//+----------------------------------------------------------------------------+
//|  Автор    : Ким Игорь В. aka KimIV,  http://www.kimiv.ru                   |
//+----------------------------------------------------------------------------+
//|  Версия   : 10.04.2008                                                     |
//|  Описание : Открывает позицию по рыночной цене.                            |
//+----------------------------------------------------------------------------+
//|  Параметры:                                                                |
//|    sy - наименование инструмента   (NULL или "" - текущий символ)          |
//|    op - операция                                                           |
//|    ll - лот                                                                |
//|    sl - уровень стоп                                                       |
//|    tp - уровень тейк                                                       |
//|    mn - MagicNumber                                                        |
//|    co - комментарий                                                        |
//+----------------------------------------------------------------------------+
void OpenPosition(string sy, int op, double ll, double sl=0, double tp=0, int mn=0, string co="") {
  color    clOpen;
  datetime ot;
  double   pp, pa, pb;
  int      dg, err, it, ticket=0;

  if (sy=="" || sy=="0") sy=Symbol();
  if (co=="") co=WindowExpertName()+" "+GetNameTF(Period());
  for (it=1; it<=NumberOfTry; it++) {
    if (!IsTesting() && (!IsExpertEnabled() || IsStopped())) {
      Print("OpenPosition(): Остановка работы функции");
      break;
    }
    while (!IsTradeAllowed()) Sleep(5000);
    RefreshRates();
    dg=MarketInfo(sy, MODE_DIGITS);
    pa=MarketInfo(sy, MODE_ASK);
    pb=MarketInfo(sy, MODE_BID);
    if (op==OP_BUY) pp=pa; else pp=pb;
    pp=NormalizeDouble(pp, dg);
    ot=TimeCurrent();
    if (MarketWatch)
      ticket=OrderSend(sy, op, ll, pp, Slippage, 0, 0, co, mn, 0, CLR_NONE);
    else
      ticket=OrderSend(sy, op, ll, pp, Slippage, sl, tp, co, mn, 0, CLR_NONE);
    if (ticket>0) {
      if (UseSound) PlaySound(SoundSuccess); break;
    } else {
      err=GetLastError();
      if (UseSound) PlaySound(SoundError);
      if (pa==0 && pb==0) Message("Проверьте в Обзоре рынка наличие символа "+sy);
      // Вывод сообщения об ошибке
      Print("Error(",err,") opening position: ",ErrorDescription(err),", try ",it);
      Print("Ask=",pa," Bid=",pb," sy=",sy," ll=",ll," op=",GetNameOP(op),
            " pp=",pp," sl=",sl," tp=",tp," mn=",mn);
      // Блокировка работы советника
      if (err==2 || err==64 || err==65 || err==133) {
        gbDisabled=True; break;
      }
      // Длительная пауза
      if (err==4 || err==131 || err==132) {
        Sleep(1000*300); break;
      }
      if (err==128 || err==142 || err==143) {
        Sleep(1000*66.666);
        if (ExistPositions(sy, op, mn, ot)) {
          if (UseSound) PlaySound(SoundSuccess); break;
        }
      }
      if (err==140 || err==148 || err==4110 || err==4111) break;
      if (err==141) Sleep(1000*100);
      if (err==145) Sleep(1000*17);
      if (err==146) while (IsTradeContextBusy()) Sleep(1000*11);
      if (err!=135) Sleep(1000*7.7);
    }
  }
  if (MarketWatch && ticket>0 && (sl>0 || tp>0)) {
    if (OrderSelect(ticket, SELECT_BY_TICKET)) ModifyOrder(-1, sl, tp);
  }
}
//+----------------------------------------------------------------------------+
//|  Автор    : Ким Игорь В. aka KimIV,  http://www.kimiv.ru                   |
//+----------------------------------------------------------------------------+
//|  Версия   : 06.03.2008                                                     |
//|  Описание : Возвращает флаг существования позиций                          |
//+----------------------------------------------------------------------------+
//|  Параметры:                                                                |
//|    sy - наименование инструмента   (""   - любой символ,                   |
//|                                     NULL - текущий символ)                 |
//|    op - операция                   (-1   - любая позиция)                  |
//|    mn - MagicNumber                (-1   - любой магик)                    |
//|    ot - время открытия             ( 0   - любое время открытия)           |
//+----------------------------------------------------------------------------+
bool ExistPositions(string sy="", int op=-1, int mn=-1, datetime ot=0) {
  int i, k=OrdersTotal();

  if (sy=="0") sy=Symbol();
  for (i=0; i<k; i++) {
    if (OrderSelect(i, SELECT_BY_POS, MODE_TRADES)) {
      if (OrderSymbol()==sy || sy=="") {
        if (OrderType()==OP_BUY || OrderType()==OP_SELL) {
          if (op<0 || OrderType()==op) {
            if (mn<0 || OrderMagicNumber()==mn) {
              if (ot<=OrderOpenTime()) return(True);
            }
          }
        }
      }
    }
  }
  return(False);
}
//+----------------------------------------------------------------------------+
//|  Автор    : Ким Игорь В. aka KimIV,  http://www.kimiv.ru                   |
//+----------------------------------------------------------------------------+
//|  Версия   : 28.11.2006                                                     |
//|  Описание : Модификация одного предварительно выбранного ордера.           |
//+----------------------------------------------------------------------------+
//|  Параметры:                                                                |
//|    pp - цена установки ордера                                              |
//|    sl - ценовой уровень стопа                                              |
//|    tp - ценовой уровень тейка                                              |
//|    ex - дата истечения                                                     |
//+----------------------------------------------------------------------------+
void ModifyOrder(double pp=-1, double sl=0, double tp=0, datetime ex=0) {
  bool   fm;
  double op, pa, pb, os, ot;
  int    dg=MarketInfo(OrderSymbol(), MODE_DIGITS), er, it;

  if (pp<=0) pp=OrderOpenPrice();
  if (sl<0 ) sl=OrderStopLoss();
  if (tp<0 ) tp=OrderTakeProfit();
  
  pp=NormalizeDouble(pp, dg);
  sl=NormalizeDouble(sl, dg);
  tp=NormalizeDouble(tp, dg);
  op=NormalizeDouble(OrderOpenPrice() , dg);
  os=NormalizeDouble(OrderStopLoss()  , dg);
  ot=NormalizeDouble(OrderTakeProfit(), dg);

  if (pp!=op || sl!=os || tp!=ot) {
    for (it=1; it<=NumberOfTry; it++) {
      if (!IsTesting() && (!IsExpertEnabled() || IsStopped())) break;
      while (!IsTradeAllowed()) Sleep(5000);
      RefreshRates();
      fm=OrderModify(OrderTicket(), pp, sl, tp, ex, CLR_NONE);
      if (fm) {
        if (UseSound) PlaySound(SoundSuccess); break;
      } else {
        er=GetLastError();
        if (UseSound) PlaySound(SoundError);
        pa=MarketInfo(OrderSymbol(), MODE_ASK);
        pb=MarketInfo(OrderSymbol(), MODE_BID);
        Print("Error(",er,") modifying order: ",ErrorDescription(er),", try ",it);
        Print("Ask=",pa,"  Bid=",pb,"  sy=",OrderSymbol(),
              "  op="+GetNameOP(OrderType()),"  pp=",pp,"  sl=",sl,"  tp=",tp);
        Sleep(1000*10);
      }
    }
  }
}
//+----------------------------------------------------------------------------+
//|  Автор    : Ким Игорь В. aka KimIV,  http://www.kimiv.ru                   |
//+----------------------------------------------------------------------------+
//|  Версия   : 18.07.2008                                                     |
//|  Описание : Возвращает одно из двух значений взависимости от условия.      |
//+----------------------------------------------------------------------------+
color IIFc(bool condition, color ifTrue, color ifFalse) {
  if (condition) return(ifTrue); else return(ifFalse);
}
//+----------------------------------------------------------------------------+
//| Автор    : Ким Игорь В. aka KimIV,  http://www.kimiv.ru                    |
//+----------------------------------------------------------------------------+
//| Версия   : 07.10.2006                                                      |
//| Описание : Поиск ближайшего фрактала.                                      |
//+----------------------------------------------------------------------------+
//| Параметры:                                                                 |
//|   sy - наименование инструмента     (NULL - текущий символ)                |
//|   tf - таймфрейм                    (  0  - текущий ТФ)                    |
//|   mode - тип фрактала               (MODE_LOWER|MODE_UPPER)                |
//+----------------------------------------------------------------------------+
double FindNearFractal(string sy="0", int tf=0, int mode=MODE_LOWER) {
  if (sy=="" || sy=="0") sy=Symbol();
  double f=0;
  int d=MarketInfo(sy, MODE_DIGITS), s;
  if (d==0) if (StringFind(sy, "JPY")<0) d=4; else d=2;

  for (s=3; s<100; s++) {
    f=iFractals(sy, tf, mode, s);
    if (f!=0) return(NormalizeDouble(f, d));
  }
  Print("FindNearFractal(): Фрактал не найден");
  return(0);
}