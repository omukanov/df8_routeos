# -*- coding: utf-8 -*-
from telebot import TeleBot, types
from routeros import login
import config


class DF8RouteOS:
    def __init__(self, tlg_token: str = None, tlg_user_id: str = None, route_ip: str = None, route_user: str = None,
                 route_password: str = None):
        self.tlg_token = tlg_token
        self.tlg_user_id = tlg_user_id
        self.route_ip = route_ip
        self.route_user = route_user
        self.route_password = route_password
        self.bot = TeleBot(config.tlg_token)
        self.rules = self.get_rule() if config.get_rule_from_router else config.rules

        @self.bot.message_handler(commands=['start'])
        def start_message(message):
            if str(message.chat.id) != config.tlg_user_id:
                self.bot.send_message(message.chat.id, 'Fuck YOU')
            else:
                keyboard = types.InlineKeyboardMarkup()
                for rule in self.rules:
                    keyboard.add(types.InlineKeyboardButton(text=f'{rule}', callback_data=rule))
                self.bot.send_message(message.chat.id, text="Rules:", reply_markup=keyboard)

        @self.bot.callback_query_handler(func=lambda call: True)
        def callback_inline(call):
            if call.message:
                rule = call.data
                rule_data = self.find_nat_by_rule_name(rule)
                action = 'enable' if rule_data['disabled'] == 'true' else 'disable'
                if rule_data:
                    router_os = login(config.route_user, config.route_password, config.route_ip)
                    router_os(f'/ip/firewall/nat/{action}', **{'.id': rule_data['.id']})
                    router_os.close()
                    self.bot.send_message(call.message.chat.id, f'Rule: "*{rule}*" change state to "*{action}*"',
                                          parse_mode='Markdown')
                    self.bot.answer_callback_query(callback_query_id=call.id, text=f'Success')
                else:
                    self.bot.answer_callback_query(callback_query_id=call.id, text=f'Nat rule name: "{rule}" not found',
                                                   show_alert=True)

        self.bot.polling(none_stop=True)

    def auth(self, messages: str):
        for m in messages:
            if str(m.chat.id) == config.tlg_user_id:
                self.listener(messages)
            else:
                self.bot.send_message(m.chat.id, 'Fuck YOU')

    @staticmethod
    def find_nat_by_rule_name(comment):
        router_os = login(config.route_user, config.route_password, config.route_ip)
        nat_rule = router_os.query('/ip/firewall/nat/print').equal(comment=comment)
        router_os.close()
        if nat_rule:
            return nat_rule[0]

    @staticmethod
    def get_rule():
        rules = []
        router_os = login(config.route_user, config.route_password, config.route_ip)
        nat_rule = router_os.__call__('/ip/firewall/nat/print')
        for rule in nat_rule:
            rules.append(rule['comment'])
        router_os.close()

        return rules


if __name__ == '__main__':
    tlg_route_os = DF8RouteOS(tlg_token=config.tlg_token, tlg_user_id=config.tlg_user_id, route_ip=config.route_ip,
                              route_user=config.route_user, route_password=config.route_password)
