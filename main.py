import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

class CurrencyConverter:
    def __init__(self):
        self.cache_date = None
        self.rates = {'USD': None, 'CNY': None}
        
    def get_cbr_rates(self):
        today = datetime.now().date()
        if self.cache_date == today and all(self.rates.values()):
            return
            
        try:
            date_str = datetime.now().strftime("%d/%m/%Y")
            url = f'https://www.cbr.ru/scripts/XML_daily.asp?date_req={date_str}'
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            root = ET.fromstring(response.content)
            
            for valute in root.findall('Valute'):
                valute_id = valute.get('ID')
                if valute_id == 'R01235':  # USD
                    value = valute.find('Value').text.replace(',', '.')
                    nominal = int(valute.find('Nominal').text)
                    self.rates['USD'] = Decimal(value) / nominal
                elif valute_id == 'R01375':  # CNY
                    value = valute.find('Value').text.replace(',', '.')
                    nominal = int(valute.find('Nominal').text)
                    self.rates['CNY'] = Decimal(value) / nominal
                    
            self.cache_date = today
        except Exception as e:
            print(f"Ошибка получения курсов: {e}")
            raise

    def convert(self, amount, from_currency, to_currency):
        if from_currency == to_currency:
            return Decimal(amount).quantize(Decimal('0.01'), ROUND_HALF_UP)
            
        if from_currency == 'RUB':
            rate = 1 / self.rates[to_currency]
        elif to_currency == 'RUB':
            rate = self.rates[from_currency]
        else:
            rate = self.rates[from_currency] / self.rates[to_currency]
            
        return (Decimal(amount) * rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

def get_valid_input(prompt, input_type=Decimal):
    while True:
        try:
            user_input = input(prompt)
            if input_type == Decimal:
                user_input = user_input.replace(',', '.')
            value = input_type(user_input)
            if value < 0:
                raise ValueError
            return value
        except ValueError:
            print("Некорректный ввод. Пожалуйста, введите положительное число.")

def main():
    converter = CurrencyConverter()
    
    try:
        converter.get_cbr_rates()
        usd_rate = converter.rates['USD']
        cny_rate = converter.rates['CNY']
        
        print("\nТекущие курсы ЦБ РФ:")
        print(f"1 USD = {usd_rate:.2f} RUB")
        print(f"1 CNY = {cny_rate:.2f} RUB")
        
        registrations = get_valid_input("Число удачных регистраций: ", int)
        sms_used = get_valid_input("Число потраченных SMS: ", int)
        number_cost_per_cny = get_valid_input("Стоимость одного номера в юанях: ")
        
        # Расчет общей стоимости номеров
        total_number_cost_cny = number_cost_per_cny * registrations
        
        # Расчет SMS комиссии и конвертация в CNY
        sms_cost_rub = Decimal(sms_used) * Decimal('1.5')
        sms_cost_cny = converter.convert(sms_cost_rub, 'RUB', 'CNY')
        
        # Общая себестоимость в CNY
        total_cost_cny = total_number_cost_cny + sms_cost_cny
        
        # Себестоимость на одну регистрацию
        cost_per_registration_cny = total_cost_cny / registrations
        
        # Конвертация в другие валюты
        cost_per_registration_rub = converter.convert(cost_per_registration_cny, 'CNY', 'RUB')
        cost_per_registration_usd = converter.convert(cost_per_registration_cny, 'CNY', 'USD')
        
        # Вывод результатов
        print("\n" + "="*50)
        print(f"{'СЕБЕСТОИМОСТЬ НА ОДНУ РЕГИСТРАЦИЮ':^50}")
        print("="*50)
        print(f"{'CNY:':<10}{cost_per_registration_cny:.2f} ¥")
        print(f"{'RUB:':<10}{cost_per_registration_rub:.2f} ₽")
        print(f"{'USD:':<10}{cost_per_registration_usd:.2f} $\n")
        
        print(f"{'ОБЩИЕ ЗАТРАТЫ':^50}")
        print("-"*50)
        print(f"Стоимость номеров: {total_number_cost_cny:.2f} ¥")
        print(f"SMS комиссия: {sms_cost_cny:.2f} ¥ ({sms_cost_rub:.2f} ₽)")
        print(f"Всего затрат:")
        print(f"  CNY: {total_cost_cny:.2f} ¥")
        print(f"  RUB: {converter.convert(total_cost_cny, 'CNY', 'RUB'):.2f} ₽")
        print(f"  USD: {converter.convert(total_cost_cny, 'CNY', 'USD'):.2f} $")

    except Exception as e:
        print(f"Произошла ошибка: {e}")

if __name__ == "__main__":
    main()