#Module-Specific definitions
%define mod_name mod_gnutls
%define mod_conf B11_%{mod_name}.conf
%define mod_so %{mod_name}.so

Summary:	Mod_gnutls is a DSO module for the apache Web server
Name:		apache-%{mod_name}
Version:	0.2.0
Release:	%mkrel 2
Group:		System/Servers
License:	Apache License
URL:		http://www.outoforder.cc/projects/apache/mod_gnutls/
Source0:	http://www.outoforder.cc/downloads/mod_gnutls/%{mod_name}-%{version}.tar.bz2
Source1:	%{mod_conf}
Patch0:		mod_gnutls-no_ap_prefix.diff
Patch1:		mod_gnutls-modname.diff
Patch2:		mod_gnutls-cert_path.diff
Requires(post): gnutls
Requires(pre): rpm-helper
Requires(postun): rpm-helper
Requires(pre):	apache-conf >= 2.2.0
Requires(pre):	apache >= 2.2.0
Requires:	apache-conf >= 2.2.0
Requires:	apache >= 2.2.0
BuildRequires:	apache-devel >= 2.2.0
BuildRequires:	apr_memcache-devel
BuildRequires:	gnutls-devel
BuildRoot:	%{_tmppath}/%{name}-%{version}-%{release}-buildroot

%description
mod_gnutls uses the GnuTLS library to provide SSL v3, TLS 1.0 and TLS 1.1
encryption for Apache HTTPD. It is similar to mod_ssl in purpose, but does not
use OpenSSL.

%prep

%setup -q -n %{mod_name}-%{version}
%patch0 -p0
%patch1 -p0
%patch2 -p0

cp %{SOURCE1} %{mod_conf}

# lib64 fixes
perl -pi -e "s|/lib\ |/%{_lib}\ |g" m4/apr_memcache.m4
perl -pi -e "s|/lib\b|/%{_lib}|g" m4/apr_memcache.m4
perl -pi -e "s|/lib/|/%{_lib}/|g" m4/apr_memcache.m4

# only make the binary
perl -pi -e "s|^SUBDIRS.*|SUBDIRS = src|g" Makefile.am

%build
#sh autogen.sh
rm -f configure
libtoolize --force --copy; aclocal -I m4; autoheader; automake --add-missing --copy --foreign; autoconf
rm -rf autom4te.cache

%configure2_5x \
    --with-apxs=%{_sbindir}/apxs \
    --with-apr-memcache=%{_prefix}

%make

%install
[ "%{buildroot}" != "/" ] && rm -rf %{buildroot}

install -d %{buildroot}%{_libdir}/apache-extramodules
install -d %{buildroot}%{_sysconfdir}/httpd/conf/%{mod_name}
install -d %{buildroot}%{_sysconfdir}/httpd/modules.d

install -m0755 src/.libs/*.so %{buildroot}%{_libdir}/apache-extramodules/
install -m0644 %{mod_conf} %{buildroot}%{_sysconfdir}/httpd/modules.d/%{mod_conf}

%post
rsafile="%{_sysconfdir}/httpd/conf/%{mod_name}/rsafile"
dhfile="%{_sysconfdir}/httpd/conf/%{mod_name}/dhfile"

if ! [ -f ${rsafile} -o -f ${dhfile} ]; then
    echo "Creating certificates (this can take quite some time) ..."
    %{_bindir}/certtool --generate-privkey --bits 512 --outfile ${rsafile}
    %{_bindir}/certtool --generate-dh-params --bits 1024 --outfile ${dhfile}
    chmod 640 ${rsafile} ${dhfile}
    chown apache:root ${rsafile} ${dhfile}
    echo "Done ..."
fi

if [ -f %{_var}/lock/subsys/httpd ]; then
    %{_initrddir}/httpd restart 1>&2;
fi

%postun
if [ "$1" = "0" ]; then
    if [ -f %{_var}/lock/subsys/httpd ]; then
        %{_initrddir}/httpd restart 1>&2
    fi
fi

%clean
[ "%{buildroot}" != "/" ] && rm -rf %{buildroot}

%files
%defattr(-,root,root)
%doc LICENSE NOTICE README
%attr(0750,root,root) %dir %{_sysconfdir}/httpd/conf/%{mod_name}
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/httpd/modules.d/%{mod_conf}
%attr(0755,root,root) %{_libdir}/apache-extramodules/%{mod_so}
