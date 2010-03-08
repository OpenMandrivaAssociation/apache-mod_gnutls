#Module-Specific definitions
%define mod_name mod_gnutls
%define mod_conf B11_%{mod_name}.conf
%define mod_so %{mod_name}.so

Summary:	DSO module for the apache Web server
Name:		apache-%{mod_name}
Version:	0.5.5
Release:	%mkrel 4
Group:		System/Servers
License:	Apache License
URL:		http://www.outoforder.cc/projects/apache/mod_gnutls/
Source0:	http://www.outoforder.cc/downloads/mod_gnutls/%{mod_name}-%{version}.tar.bz2
Source1:	%{mod_conf}
Patch0:		mod_gnutls-0.4.2.1-change-module-name.diff
Patch1:		mod_gnutls-apu13.diff
Patch2:		mod_gnutls-no_rpath.diff
Patch3:		mod_gnutls-0.5.4-gnutls-2.8.patch
# sent upstream : http://issues.outoforder.cc/view.php?id=102 
Patch4:		mod_gnutls-fix_double_free.diff
Requires(post): gnutls
Requires(pre): rpm-helper
Requires(postun): rpm-helper
Requires(pre):	apache-conf >= 2.2.0
Requires(pre):	apache >= 2.2.0
Requires:	apache-conf >= 2.2.0
Requires:	apache >= 2.2.0
BuildRequires:	apache-devel >= 2.2.0
BuildRequires:	apr-util-devel >= 1.3.0
BuildRequires:	gnutls-devel >= 2.2.1
BuildRoot:	%{_tmppath}/%{name}-%{version}-%{release}-buildroot

%description
mod_gnutls uses the GnuTLS library to provide SSL v3, TLS 1.0 and TLS 1.1
encryption for Apache HTTPD. It is similar to mod_ssl in purpose, but does not
use OpenSSL.

%prep
%setup -q -n %{mod_name}-%{version}
%patch0 -p1
%patch1 -p0
%patch2 -p0
%patch3 -p0
%patch4 -p0

cp %{SOURCE1} %{mod_conf}

# only make the binary
perl -pi -e "s|^SUBDIRS.*|SUBDIRS = src|g" Makefile.am

%build
autoreconf
%configure2_5x --localstatedir=/var/lib \
    --with-apxs=%{_sbindir}/apxs \
    --with-apr-memcache-libs=%{_libdir}

%make

%install
rm -rf %{buildroot}

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
rm -rf %{buildroot}

%files
%defattr(-,root,root)
%doc LICENSE NOTICE README
%attr(0750,root,root) %dir %{_sysconfdir}/httpd/conf/%{mod_name}
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/httpd/modules.d/%{mod_conf}
%attr(0755,root,root) %{_libdir}/apache-extramodules/%{mod_so}
