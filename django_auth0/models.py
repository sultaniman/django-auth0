from django.db import models, IntegrityError, transaction
from django.contrib.auth.models import (BaseUserManager,
        AbstractBaseUser, PermissionsMixin)
from django.forms import model_to_dict
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.signals import pre_save, pre_delete
from django.contrib.auth.models import Group
from django.dispatch import receiver
from django.utils import timezone


class Auth0UserManager(BaseUserManager):

    def create(self, *args, **kwargs):
        return self.create_user(*args, **kwargs)

    def get_or_create(self, **kwargs):
        try:
            return self.get(**kwargs), False
        except self.model.DoesNotExist:
            return self.create(**kwargs), True

    def update_or_create(self, defaults=None, **kwargs):
        defaults = defaults or {}
        try:
            user = self.get(**kwargs)
        except self.model.DoesNotExist:
            kwargs.update(defaults)
            return self.create(**kwargs), True

        if 'password' in defaults:
            user.set_password(defaults.pop('password'))
        for k, v in defaults.items():
            setattr(user, k, v)
        user.save(using=self._db)
        user._remove_raw_password()
        return user, False

    def _create_user(self, email, given_name, surname, password):
        if not email:
            raise ValueError("Users must have an email address")

        if not given_name or not surname:
            raise ValueError("Users must provide a given name and a surname")

        user = self.model(email=Auth0UserManager.normalize_email(email),
            given_name=given_name, surname=surname)

        user.set_password(password)
        user.save(using=self._db)
        user._remove_raw_password()
        return user

    def create_user(self, email, given_name=None, surname=None, password=None,
                    first_name=None, last_name=None):
        if first_name and not given_name:
            given_name = first_name
        if last_name and not surname:
            surname = last_name

        return self._create_user(email=email, given_name=given_name, surname=surname,
                          password=password)

    def create_superuser(self, **kwargs):
        user = self.create_user(**kwargs)
        user.is_admin = True
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        user._remove_raw_password()
        return user

    def delete(self, *args, **kwargs):
        for user in self.get_queryset():
            user.delete(*args, **kwargs)

        # Clear the result cache, in case this QuerySet gets reused.
        self._result_cache = None

    def sync_accounts_from_stormpath(self, sync_groups=True):
        """ :arg sync_groups: WARNING!!! Groups will be deleted from stormpath
                                if not present locally when user logs in!
        Sync accounts from stormpath -> local database.
        This may take a long time, depending on how many users you have in your
        Stormpath application. It also makes numerous database queries.
        This method updates local users from stormpath or creates new ones
        where the user does not exist locally. This is an additive operation,
        meaning it should delete no data from the local database OR stormpath.
        """
        if sync_groups:
            sp_groups = [g.name for g in APPLICATION.groups]
            db_groups = set(Group.objects.all().values_list('name', flat=True))
            missing_from_db = set(sp_groups).difference(db_groups)
            if missing_from_db:
                groups_to_create = []
                for g_name in missing_from_db:
                    groups_to_create.append(Group(name=g_name))
                Group.objects.bulk_create(groups_to_create)

        for account in APPLICATION.accounts:
            try:
                user = StormpathUser.objects.get(email=account.email)
                created = True
            except StormpathUser.DoesNotExist:
                user = StormpathUser()
                created = True
            user._mirror_data_from_stormpath_account(account)
            user.set_unusable_password()

            if created:
                user._save_db_only()

            if sync_groups:
                users_sp_groups = [g.name for g in account.groups]
                user.groups = Group.objects.filter(name__in=users_sp_groups)
            user._save_db_only()

    delete.alters_data = True
    delete.queryset_only = True


class Auth0BaseUser(AbstractBaseUser, PermissionsMixin):

    class Meta:
        abstract = True

    username = models.CharField(
        max_length=255,
        help_text='<backend>-<user_id>',
        unique=True
    )

    first_name = models.CharField(_('first name'), max_length=30, blank=True)
    last_name = models.CharField(_('last name'), max_length=30, blank=True)
    email = models.EmailField(_('email address'))
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_(
            'Designates whether this user should be treated as active. '
            'Unselect this instead of deleting accounts.'
        ),
    )
    is_staff = models.BooleanField(
        _('staff status'),
        default=False,
        help_text=_('Designates whether the user can log into this admin site.'),
    )
    is_admin = models.BooleanField(default=False)
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)

    objects = Auth0UserManager()

    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    PASSWORD_FIELD = 'password'

    # Auth0 -> local field mapping
    AUTH0_FIELD_MAPPING = {
        'user_id': 'username',
        'name': 'email',
        'email': 'email',
        'app_metadata': {
            'first_name': 'first_name',
            'last_name': 'last_name',
        },
        'created_at': 'date_joined',
    }

    def _mirror_data_from_db_user(self, account, data):
        for field in self.EXCLUDE_FIELDS:
            if field in data:
                del data[field]

        if data['is_active']:
            account.status = account.STATUS_ENABLED
        elif data['is_verified']:
            account.status = account.STATUS_DISABLED
        else:
            account.status = account.STATUS_UNVERIFIED

        if 'is_active' in data:
            del data['is_active']

        for key in data:
            if key in self.STORMPATH_BASE_FIELDS:
                account[key] = data[key]
            else:
                account.custom_data[self.DJANGO_PREFIX + key] = data[key]

        return account

    def _mirror_data_from_stormpath_account(self, account):
        for field in self.STORMPATH_BASE_FIELDS:
            # The password is not sent via the API
            # so we take care here to not try and
            # mirror it because it's not there
            if field != 'password':
                self.__setattr__(field, account[field])
        for key in account.custom_data.keys():
            self.__setattr__(key.split(self.DJANGO_PREFIX)[0], account.custom_data[key])

        if account.status == account.STATUS_ENABLED:
            self.is_active = True
            self.is_verified = not get_default_is_active()
        else:
            self.is_active = False
            if account.status == account.STATUS_UNVERIFIED:
                self.is_verified = False

    def _save_sp_group_memberships(self, account):
        try:
            db_groups = self.groups.values_list('name', flat=True)
            for g in db_groups:
                if not account.has_group(g):
                    account.add_group(g)

            account.save()

            for gm in account.group_memberships:
                if gm.group.name not in db_groups:
                    gm.delete()
        except Exception:
            raise IntegrityError("Unable to save group memberships.")

    def _create_stormpath_user(self, data, raw_password):
        data['password'] = raw_password
        account = APPLICATION.accounts.create(data)
        self._save_sp_group_memberships(account)
        return account

    def _update_stormpath_user(self, data, raw_password):
        # if password has changed
        if raw_password:
            data['password'] = raw_password
        else:
            # don't set the password if it hasn't changed
            del data['password']
        try:
            acc = APPLICATION.accounts.get(data.get('href'))
            # materialize it
            acc.email

            acc = self._mirror_data_from_db_user(acc, data)
            acc.save()
            self._save_sp_group_memberships(acc)
            return acc
        except StormpathError as e:
            if e.status == 404:
                raise self.DoesNotExist('Could not find Stormpath User.')
            else:
                raise e
        finally:
            self._remove_raw_password()

    def get_full_name(self):
        return "%s %s" % (self.given_name, self.surname)

    def get_short_name(self):
        return self.email

    def __unicode__(self):
        return self.get_full_name()

    def _update_for_db_and_stormpath(self, *args, **kwargs):
        try:
            with transaction.atomic():
                super(Auth0BaseUser, self).save(*args, **kwargs)
                self._update_stormpath_user(model_to_dict(self), self._get_raw_password())
        except StormpathError:
            raise
        except ObjectDoesNotExist:
            self.delete()
            raise
        except Exception:
            raise

    def _create_for_db_and_stormpath(self, *args, **kwargs):
        try:
            with transaction.atomic():
                super(Auth0BaseUser, self).save(*args, **kwargs)
                account = self._create_stormpath_user(model_to_dict(self), self._get_raw_password())
                self.href = account.href
                self.username = account.username
                self.save(*args, **kwargs)
        except StormpathError:
            raise
        except Exception:
            # we're not sure if we have a href yet, hence we
            # filter by email
            accounts = APPLICATION.accounts.search({'email': self.email})
            if accounts:
                accounts[0].delete()
            raise

    def _save_db_only(self, *args, **kwargs):
        super(Auth0BaseUser, self).save(*args, **kwargs)

    def _remove_raw_password(self):
        """We need to send a raw password to Stormpath. After an Account is saved on Stormpath
        we need to remove the raw password field from the local object"""

        try:
            del self.raw_password
        except AttributeError:
            pass

    def _get_raw_password(self):
        try:
            return self.raw_password
        except AttributeError:
            return None

    def set_password(self, raw_password):
        """We don't want to keep passwords locally"""
        self.set_unusable_password()
        self.raw_password = raw_password

    def check_password(self, raw_password):
        try:
            acc = APPLICATION.authenticate_account(self.username, raw_password)
            return acc is not None
        except StormpathError as e:
            # explicity check to see if password is incorrect
            if e.code == 7100:
                return False
            raise e

    def save(self, *args, **kwargs):
        self.username = getattr(self, self.USERNAME_FIELD)
        # Are we updating an existing User?
        if self.id:
            self._update_for_db_and_stormpath(*args, **kwargs)
        # Or are we creating a new user?
        else:
            self._create_for_db_and_stormpath(*args, **kwargs)

    def delete(self, *args, **kwargs):
        with transaction.atomic():
            href = self.href
            super(Auth0BaseUser, self).delete(*args, **kwargs)
            try:
                account = APPLICATION.accounts.get(href)
                account.delete()
            except StormpathError:
                raise


class Auth0User(Auth0BaseUser):
    pass


@receiver(pre_save, sender=Group)
def save_group_to_auth0(sender, instance, **kwargs):
    try:
        if instance.pk is None:
            # creating a new group
            APPLICATION.groups.create({'name': instance.name})
        else:
            # updating an existing group
            old_group = Group.objects.get(pk=instance.pk)
            remote_groups = APPLICATION.groups.search({'name': old_group.name})
            if len(remote_groups) is 0:
                # group existed locally but not on Stormpath, create it
                APPLICATION.groups.create({'name': instance.name})
                return

            remote_group = remote_groups[0]

            if remote_group.name == instance.name:
                return  # nothing changed

            remote_group.name = instance.name
            remote_group.save()

    except StormpathError as e:
        raise IntegrityError(e)


@receiver(pre_delete, sender=Group)
def delete_group_from_stormpath(sender, instance, **kwargs):
    try:
        APPLICATION.groups.search({'name': instance.name})[0].delete()
    except StormpathError as e:
        raise IntegrityError(e)
