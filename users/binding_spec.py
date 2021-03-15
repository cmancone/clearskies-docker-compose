import clearskies


class BindingSpec(clearskies.binding_specs.WSGI):
    def provide_authentication(self, input_output, environment):
        return clearskies.authentication.SecretBearer(
            input_output,
            environment.get('users_authentication_secret')
        )
