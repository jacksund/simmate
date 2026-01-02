# -*- coding: utf-8 -*-

from django.http import HttpResponseRedirect

from simmate.website.htmx.components import HtmxComponent


class TokenBalanceForm(HtmxComponent):

    template_name = "project_management/wallet/token_balance_form.html"

    def submit(self):

        wallet = self.request.user.wallet

        wallet.adjust_tokens(
            token_amount=float(self.form_data["token_amount"]),
            sending_user=self.request.user,
        )

        # just refresh the current page to get the updated balance
        return HttpResponseRedirect(self.initial_context.request.path_info)
