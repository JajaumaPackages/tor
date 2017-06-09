%global _hardened_build 1

%global toruser     toranon
%global torgroup    toranon
%global homedir     %{_localstatedir}/lib/tor
%global logdir      %{_localstatedir}/log/tor
%global rundir      /run/tor

%if 0%{?fedora} || 0%{?rhel} >= 8
%bcond_without libsystemd
%else
%bcond_with libsystemd
%endif

%ifarch %{ix86} x86_64
%bcond_without libseccomp
%else
%bcond_with libseccomp
%endif

Name:       tor
Version:    0.3.0.8
Release:    1%{?dist}
Group:      System Environment/Daemons
License:    BSD
Summary:    Anonymizing overlay network for TCP
URL:        https://www.torproject.org

Source0:    https://www.torproject.org/dist/tor-%{version}.tar.gz
Source1:    https://www.torproject.org/dist/tor-%{version}.tar.gz.asc
Source2:    tor.logrotate
Source3:    tor.defaults-torrc
Source4:    tor.tmpfiles.d
Source10:   tor.service
Source11:   tor@.service
Source12:   tor-master.service
Source20:   README

Patch0:     tor-0.2.7.6-torrc-ControlSocket-and-CookieAuthFile.patch

BuildRequires:    asciidoc
BuildRequires:    libevent-devel
BuildRequires:    openssl-devel

%if 0%{with libseccomp}
# Only available on certain architectures.
BuildRequires:    libseccomp-devel
%endif

%if 0%{with libsystemd}
# Requires systemd >= 209. RHEL 7 has systemd 208.
BuildRequires:    systemd-devel
%endif

# /usr/bin/torify is now just a wrapper for torsocks and is only there for
# backwards compatibility.
Requires:         torsocks
Requires(pre):    shadow-utils
Requires(post):   systemd
Requires(preun):  systemd
Requires(postun): systemd


%description
The Tor network is a group of volunteer-operated servers that allows people to
improve their privacy and security on the Internet. Tor's users employ this
network by connecting through a series of virtual tunnels rather than making a
direct connection, thus allowing both organizations and individuals to share
information over public networks without compromising their privacy. Along the
same line, Tor is an effective censorship circumvention tool, allowing its
users to reach otherwise blocked destinations or content. Tor can also be used
as a building block for software developers to create new communication tools
with built-in privacy features.

This package contains the Tor software that can act as either a server on the
Tor network, or as a client to connect to the Tor network.


%prep
%setup -q
%patch0 -p1


%build
%configure --with-tor-user=%{toruser} --with-tor-group=%{torgroup}
make %{?_smp_mflags}


%install
make install DESTDIR=%{buildroot}
mv %{buildroot}%{_sysconfdir}/tor/torrc.sample \
    %{buildroot}%{_sysconfdir}/tor/torrc

install -D -p -m 0644 %{SOURCE20} %{buildroot}%{_sysconfdir}/tor/README

mkdir -p %{buildroot}%{logdir}
mkdir -p %{buildroot}%{homedir}
mkdir -p %{buildroot}%{rundir}

install -D -p -m 0644 %{SOURCE10} %{buildroot}%_unitdir/tor.service
install -D -p -m 0644 %{SOURCE11} %{buildroot}%_unitdir/tor@.service
install -D -p -m 0644 %{SOURCE12} %{buildroot}%_unitdir/tor-master.service
install -D -p -m 0644 %{SOURCE2}  %{buildroot}%{_sysconfdir}/logrotate.d/tor
install -D -p -m 0644 %{SOURCE3}  %{buildroot}%{_datadir}/tor/defaults-torrc
install -D -p -m 0644 %{SOURCE4}  %{buildroot}%{_tmpfilesdir}/tor.conf

%if 0%{without libsystemd}
# Some features are not available for systemd 208 on RHEL 7.
sed -i %{buildroot}%_unitdir/tor.service \
    -i %{buildroot}%_unitdir/tor@.service \
    -e 's/^Type=.*/Type=simple/g' \
    -e '/^NotifyAccess=.*/d' \
    -e '/^WatchdogSec=.*/d' \
    -e 's#^ProtectHome=.*#InaccessibleDirectories=/home\nInaccessibleDirectories=/root\nInaccessibleDirectories=/run/user#g' \
    -e 's#^ProtectSystem=.*#ReadOnlyDirectories=/boot\nReadOnlyDirectories=/etc\nReadOnlyDirectories=/usr#g'
%endif

# Install docs manually.
rm -rf %{buildroot}%{_datadir}/doc

%check
make check

%pre
getent group %{torgroup} >/dev/null || groupadd -r %{torgroup}
getent passwd %{toruser} >/dev/null || \
    useradd -r -s /sbin/nologin -d %{homedir} -M \
    -c 'Tor anonymizing user' -g %{torgroup} %{toruser}
exit 0

%post
%systemd_post tor.service

%preun
%systemd_preun tor.service
%systemd_preun tor-master.service

%postun
systemctl daemon-reload >/dev/null 2>&1 || :
if [ $1 -ge 1 ]; then
    # Use restart instead of try-restart, as tor-master may be "inactive" even
    # when there are tor.service and tor@.service instances running.
    systemctl restart tor-master.service >/dev/null 2>&1 || :
fi


%files
%doc LICENSE README ChangeLog ReleaseNotes doc/HACKING doc/*.html
%{_bindir}/tor
%{_bindir}/tor-gencert
%{_bindir}/tor-resolve
%{_bindir}/torify
%{_mandir}/man1/tor.1*
%{_mandir}/man1/tor-gencert.1*
%{_mandir}/man1/tor-resolve.1*
%{_mandir}/man1/torify.1*
%dir %{_datadir}/tor
%{_datadir}/tor/defaults-torrc
%{_datadir}/tor/geoip
%{_datadir}/tor/geoip6
%{_tmpfilesdir}/tor.conf
%{_unitdir}/tor.service
%{_unitdir}/tor@.service
%{_unitdir}/tor-master.service

%dir %{_sysconfdir}/tor
%{_sysconfdir}/tor/README
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/tor/torrc
%config(noreplace) %{_sysconfdir}/logrotate.d/tor

%attr(0750,%{toruser},root) %dir %{homedir}
%attr(0750,%{toruser},%{torgroup}) %dir %{logdir}
%attr(0750,%{toruser},%{torgroup}) %dir %{rundir}


%changelog
* Fri Jun 09 2017 Jajauma's Packages <jajauma@yandex.ru> - 0.3.0.8-1
- Update to latest upstream release

* Wed May 31 2017 Jajauma's Packages <jajauma@yandex.ru> - 0.3.0.7-1
- Update to latest upstream release

* Sat Apr 29 2017 Jajauma's Packages <jajauma@yandex.ru> - 0.3.0.6-2
- Run tests suite

* Sat Apr 29 2017 Jajauma's Packages <jajauma@yandex.ru> - 0.3.0.6-1
- Update to latest upstream release

* Fri Mar 03 2017 Jamie Nguyen <jamielinux@fedoraproject.org> - 0.2.9.10-1
- update to upstream release 0.2.9.10

* Sat Feb 11 2017 Fedora Release Engineering <releng@fedoraproject.org> - 0.2.8.12-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_26_Mass_Rebuild

* Tue Dec 20 2016 Jamie Nguyen <jamielinux@fedoraproject.org> - 0.2.8.12-1
- update to upstream release 0.2.8.12

* Thu Dec 08 2016 Jamie Nguyen <jamielinux@fedoraproject.org> - 0.2.8.11-1
- update to upstream release 0.2.8.11

* Wed Dec 07 2016 Jamie Nguyen <jamielinux@fedoraproject.org> - 0.2.8.10-1
- update to upstream release 0.2.8.10

* Wed Oct 19 2016 Jamie Nguyen <jamielinux@fedoraproject.org> - 0.2.8.9-1
- update to upstream release 0.2.8.9

* Sun Oct 02 2016 Jamie Nguyen <jamielinux@fedoraproject.org> - 0.2.8.8-1
- update to upstream release 0.2.8.8

* Thu Aug 25 2016 Jamie Nguyen <jamielinux@fedoraproject.org> - 0.2.8.7-1
- update to upstream release 0.2.8.7

* Sun Aug 21 2016 Jamie Nguyen <jamielinux@fedoraproject.org> - 0.2.8.6-2
- re-add patch0

* Sun Aug 21 2016 Jamie Nguyen <jamielinux@fedoraproject.org> - 0.2.8.6-1
- update to upstream release 0.2.8.6
- remove upstreamed patches

* Fri Feb 05 2016 Fedora Release Engineering <releng@fedoraproject.org> - 0.2.7.6-6
- Rebuilt for https://fedoraproject.org/wiki/Fedora_24_Mass_Rebuild

* Thu Jan 07 2016 Jamie Nguyen <jamielinux@fedoraproject.org> - 0.2.7.6-5
- make ControlSocket writable by toranon group (#1296226)

* Wed Dec 16 2015 Jamie Nguyen <jamielinux@fedoraproject.org> - 0.2.7.6-4
- fix tmpfiles.d

* Fri Dec 11 2015 Jamie Nguyen <jamielinux@fedoraproject.org> - 0.2.7.6-3
- place ControlSocket and CookieAuthFile at top of torrc for visibility

* Fri Dec 11 2015 Jamie Nguyen <jamielinux@fedoraproject.org> - 0.2.7.6-2
- some minor patch fixes

* Fri Dec 11 2015 Jamie Nguyen <jamielinux@fedoraproject.org> - 0.2.7.6-1
- update to upstream release 0.2.7.6
- use version of patches that have been accepted upstream
- add ControlSocket and CookieAuthFile to /etc/tor/torrc

* Thu Dec 10 2015 Jamie Nguyen <jamielinux@fedoraproject.org> - 0.2.7.5-6
- use ReadOnlyDirectories=/var instead of ReadOnlyDirectories=/ (#1290444)
  and other service file improvements

* Sun Dec 06 2015 Jamie Nguyen <jamielinux@fedoraproject.org> - 0.2.7.5-5
- improve systemd scriptlets

* Sun Dec 06 2015 Jamie Nguyen <jamielinux@fedoraproject.org> - 0.2.7.5-4
- add PermissionsStartOnly=yes and RestartSec=1 to service file

* Mon Nov 30 2015 Jamie Nguyen <jamielinux@fedoraproject.org> - 0.2.7.5-3
- amend README

* Mon Nov 30 2015 Jamie Nguyen <jamielinux@fedoraproject.org> - 0.2.7.5-2
- improve summary and description
- use tor-master.service to restart/reload all instances (#1286359)
- add /etc/tor/README

* Sun Nov 29 2015 Jamie Nguyen <jamielinux@fedoraproject.org> - 0.2.7.5-1
- update to upstream release 0.2.7.5

* Mon Nov 09 2015 Jamie Nguyen <jamielinux@fedoraproject.org> - 0.2.6.10-6
- amend patch so that the default of 0700 doesn't change (but instead allow
  either 0700 or 0750)

* Sun Nov 08 2015 Jamie Nguyen <jamielinux@fedoraproject.org> - 0.2.6.10-5
- allow group read of DataDirectory and change owner to root (#1279222),
  as otherwise CapabilityBoundingSet requires CAP_READ_SEARCH and SELinux
  tor_t requires dac_read_search

* Sat Oct 03 2015 Jamie Nguyen <jamielinux@fedoraproject.org> - 0.2.6.10-4
- remove NoNewPrivileges as it prevents SELinux transition
- revert to DeviceAllow instead of PrivateDevices due to SELinux denials

* Tue Sep 29 2015 Jamie Nguyen <jamielinux@fedoraproject.org> - 0.2.6.10-3
- only build with libseccomp support on ix86, x86_64

* Tue Sep 29 2015 Jamie Nguyen <jamielinux@fedoraproject.org> - 0.2.6.10-2
- improve systemd integration
- add BR: libseccomp-devel

* Mon Jul 13 2015 Jamie Nguyen <jamielinux@fedoraproject.org> - 0.2.6.10-1
- update to upstream release 0.2.6.10

* Sun Jul 12 2015 Jamie Nguyen <jamielinux@fedoraproject.org> - 0.2.6.9-5
- also fix ExecStartPre in tor@.service

* Sun Jul 12 2015 Jamie Nguyen <jamielinux@fedoraproject.org> - 0.2.6.9-4
- rebuild

* Sun Jul 12 2015 Jamie Nguyen <jamielinux@fedoraproject.org> - 0.2.6.9-3
- add missing arguments to config checks executed in ExecStartPre

* Fri Jul 03 2015 Jamie Nguyen <jamielinux@fedoraproject.org> - 0.2.6.9-2
- remove leading '-' from ReadWriteDirectories

* Fri Jun 12 2015 Jamie Nguyen <jamielinux@fedoraproject.org> - 0.2.6.9-1
- update to upstream release 0.2.6.9

* Thu May 21 2015 Jamie Nguyen <jamielinux@fedoraproject.org> - 0.2.6.8-1
- update to upstream release 0.2.6.8
- improve/harden systemd service file
- add multi-instance systemd service file (#1210837)

* Tue Apr 07 2015 Jamie Nguyen <jamielinux@fedoraproject.org> - 0.2.5.12-1
- update to upstream release 0.2.5.12

* Mon Mar 23 2015 Jamie Nguyen <jamielinux@fedoraproject.org> - 0.2.5.11-1
- update to upstream release 0.2.5.11

* Mon Oct 27 2014 Jamie Nguyen <jamielinux@fedoraproject.org> - 0.2.5.10-1
- update to upstream release 0.2.5.10

* Wed Oct 22 2014 Jamie Nguyen <jamielinux@fedoraproject.org> - 0.2.4.25-1
- update to upstream release 0.2.4.25

* Tue Sep 23 2014 Jamie Nguyen <jamielinux@fedoraproject.org> - 0.2.4.24-1
- update to upstream release 0.2.4.24

* Mon Aug 18 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.2.4.23-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_22_Mass_Rebuild

* Thu Jul 31 2014 Jamie Nguyen <jamielinux@fedoraproject.org> - 0.2.4.23-1
- update to upstream release 0.2.4.23
- CVE-2014-5117: potential for traffic-confirmation attacks

* Sun Jun 08 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.2.4.22-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_Mass_Rebuild

* Mon May 19 2014 Jamie Nguyen <jamielinux@fedoraproject.org> - 0.2.4.22-1
- update to upstream release 0.2.4.22

* Wed Mar 26 2014 Jamie Nguyen <jamielinux@fedoraproject.org> - 0.2.4.21-2
- remove `--quiet` from default systemd service file

* Tue Mar 25 2014 Jamie Nguyen <jamielinux@fedoraproject.org> - 0.2.4.21-1
- update to upstream release 0.2.4.21
- remove crazy Release numbering
- remove Obsoletes/Provides that were introduced in F19
- remove tor-tsocks.conf which has been removed completely upstream
- include new file: _datadir/tor/geoip6

* Sun Aug 04 2013 Jamie Nguyen <jamielinux@fedoraproject.org> - 0.2.3.25-1931
- add fix for new unversioned docdir

* Sun Aug 04 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.2.3.25-1930
- Rebuilt for https://fedoraproject.org/wiki/Fedora_20_Mass_Rebuild

* Sat Mar 02 2013 Jamie Nguyen <jamielinux@fedoraproject.org> 0.2.3.25-1929
- add "Log notice syslog" back to tor.defaults-torrc as recommended by
  upstream: https://bugzilla.redhat.com/show_bug.cgi?id=532373#c19
- remove unused files in git (verinfo and lastver)
- change URL to HTTPS
- disallow group read for /var/log/tor
- remove TODO as it doesn't contain any useful information

* Fri Mar 01 2013 Jamie Nguyen <jamielinux@fedoraproject.org> 0.2.3.25-1928
- increase LimitNOFILE in tor.service from 4096 to 32768, as advised by
  upstream: https://trac.torproject.org/projects/tor/ticket/8368#comment:4

* Thu Feb 28 2013 Jamie Nguyen <jamielinux@fedoraproject.org> 0.2.3.25-1927
- package should own the %%{_datadir}/tor directory

* Thu Feb 28 2013 Jamie Nguyen <jamielinux@fedoraproject.org> 0.2.3.25-1926
- remove unnecessary custom LDFLAGS

* Thu Feb 28 2013 Jamie Nguyen <jamielinux@fedoraproject.org> 0.2.3.25-1925
- remove Obsoletes/Provides for tor-doc, which was introduced in Fedora 16
- add some useful comments about the Obsoletes/Provides/Requires
- add comments about tor.logrotate, tor.defaults-torrc and tor.systemd.service

* Wed Feb 27 2013 Jamie Nguyen <jamielinux@fedoraproject.org> 0.2.3.25-1924
- whitespace changes and reorganization in the interests of readability
  and clarity

* Wed Feb 27 2013 Jamie Nguyen <jamielinux@fedoraproject.org> 0.2.3.25-1923
- mix of tabs and spaces, so remove all tabs

* Wed Feb 27 2013 Jamie Nguyen <jamielinux@fedoraproject.org> 0.2.3.25-1922
- the /var/run/tor directory is not needed so remove it, which also fixes
  bug #656707
- use %%_localstatedir instead of %%_var

* Wed Feb 27 2013 Jamie Nguyen <jamielinux@fedoraproject.org> 0.2.3.25-1921
- take a more cautious approach in the %%files section and specify filenames
  more explicitly rather than using wildcards, which also makes it easier to
  see the contents of the package

* Wed Feb 27 2013 Jamie Nguyen <jamielinux@fedoraproject.org> 0.2.3.25-1920
- remove all modifications to the default tor configuration file so that we
  can stick more closely to upstream defaults
- add /usr/share/tor/defaults-torrc file, which only contains two options:
    DataDirectory /var/lib/tor
    User toranon
- when starting the tor service, use the following options as recommended by
  upstream: --defaults-torrc /usr/share/tor/defaults-torrc -f /etc/tor/torrc

* Wed Feb 27 2013 Jamie Nguyen <jamielinux@fedoraproject.org> 0.2.3.25-1919
- split username global variable into separate toruser and torgroup global
  variables to improve spec flexibility and ease of comprehension, as well
  as matching how upstream have written their spec
- use --with-tor-user=%%toruser and --with-tor-group=%%torgroup options when
  running %%configure, as recommended by upstream

* Wed Feb 27 2013 Jamie Nguyen <jamielinux@fedoraproject.org> 0.2.3.25-1918
- after moving the tor-systemd and torify subpackages back into the main tor
  package, the %%with_noarch macro and the associated conditionals are no
  longer used so remove them

* Wed Feb 27 2013 Jamie Nguyen <jamielinux@fedoraproject.org> 0.2.3.25-1917
- add missing Provides for the obsoleted tor-doc subpackage

* Wed Feb 27 2013 Jamie Nguyen <jamielinux@fedoraproject.org> 0.2.3.25-1916
- move the torify subpackage back into the main tor package to match upstream
  expectations and user expectations (ie, yum install tor)
- remove the logic separating the documentation files for tor and torify,
  which is now no longer needed
- use --docdir option when running %%configure

* Wed Feb 27 2013 Jamie Nguyen <jamielinux@fedoraproject.org> 0.2.3.25-1915
- move the tor-systemd subpackage back into the main tor package:
  the main tor package has a hard requirement on tor-systemd, so there is no
  purpose for keeping tor-systemd separate from the main package
- remove "Requires: tor-systemd"

* Wed Feb 27 2013 Jamie Nguyen <jamielinux@fedoraproject.org> 0.2.3.25-1914
- move the tor-core subpackage back into the main tor package to match upstream
  expectations and user expectations (ie, yum install tor)

* Wed Feb 27 2013 Jamie Nguyen <jamielinux@fedoraproject.org> 0.2.3.25-1913
- the tor-systemd subpackage is a hard requirement, so remove the conditional
  that decides whether it is built

* Wed Feb 27 2013 Jamie Nguyen <jamielinux@fedoraproject.org> 0.2.3.25-1912
- amend logrotate file to match closer with upstream defaults, and removing
  references to several obsolete init systems

* Wed Feb 27 2013 Jamie Nguyen <jamielinux@fedoraproject.org> 0.2.3.25-1911
- remove tor-upstart subpackage as upstart is no longer installable within
  Fedora and renders the the subpackage obsolete

* Wed Feb 27 2013 Jamie Nguyen <jamielinux@fedoraproject.org> 0.2.3.25-1910
- remove dependency on fedora-usermgmt as it has been queued for obsoletion
  from Fedora
- add users and groups without forcing use of uid=19 as it is not necessarily
  available, nor is it required or expected by upstream
- do not remove users/groups in %%postun as the guidelines state:
  https://fedoraproject.org/wiki/Packaging:UsersAndGroups

* Wed Feb 27 2013 Jamie Nguyen <jamielinux@fedoraproject.org> 0.2.3.25-1909
- change permissions of the following files/directories to match upstream:
  /var/log/tor should be owned by toranon:toranon with 0750 permissions;
  /var/lib/tor should be owned by toranon:toranon with 0700 permissions;
  /etc/tor/torrc should be owned by root:root with 0644 permissions;

* Wed Feb 27 2013 Jamie Nguyen <jamielinux@fedoraproject.org> 0.2.3.25-1908
- remove unnecessary Requires on logrotate directory

* Wed Feb 27 2013 Jamie Nguyen <jamielinux@fedoraproject.org> 0.2.3.25-1907
- remove unnecessary BuildRoot tag
- remove unnecessary rm -rf RPM_BUILD_ROOT
- remove unnecessary %%clean
- remove unnecessary defattr's

* Wed Feb 27 2013 Jamie Nguyen <jamielinux@fedoraproject.org> 0.2.3.25-1906
- remove unnecessary %%_unitdir macro
- remove %%systemd_reqs and %%systemd_install macros, moving the parts to
  the appropriate sections to improve readability and consistency with other
  SPECS

* Wed Feb 27 2013 Jamie Nguyen <jamielinux@fedoraproject.org> 0.2.3.25-1905
- remove %%release_func macro to improve readability and consistency with
  other SPECS

* Wed Feb 13 2013 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.2.3.25-1904
- fixed torsocks requirement
- conditionalized systemd builds

* Sun Feb 10 2013 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.2.3.25-1903
- reverted "Package cleanup and various fixes"; too invasive and
  non-auditable changes which are breaking things

* Thu Feb 07 2013 Jamie Nguyen <jamielinux@fedoraproject.org> - 0.2.3.25-1902
- torify subpackage should depend on torsocks not tsocks (#908569)

* Wed Feb 06 2013 Jamie Nguyen <jamielinux@fedoraproject.org> - 0.2.3.25-1901
- add additional %%configure options for user and group
- add --defaults-torrc to systemd service to make sure sane defaults are set
  unless explicitly overridden
- remove unnecessary BuildRoot tag
- remove unnecessary rm -rf RPM_BUILD_ROOT
- remove unnecessary %%clean section
- remove unnecessary defattr's
- fix Requires for torify subpackage
- update scriptlets to latest systemd guidelines
- aesthetic changes to the SPEC for clarity and readability

* Sun Dec  9 2012 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.2.3.25-1900
- updated to 0.2.3.25

* Sat Sep 22 2012 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.2.2.39-1900
- updated to 0.2.2.29
- CVE-2012-4419: assertion failure when comparing an address with port
  0 to an address policy
- CVE-2012-4422: assertion failure in tor_timegm()
- use %%systemd macros

* Sun Aug 19 2012 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.2.2.38-1900
- updated to 0.2.2.38
- conditionalized upstart and disabled it by default

* Fri Jul 27 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.2.2.37-1801
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Tue Jun 12 2012 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.2.2.37-1800
- updated to 0.2.2.37

* Sat May 26 2012 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.2.2.36-1800
- updated to 0.2.2.36

* Fri Apr 13 2012 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.2.2.35-1800
- build with -fPIE

* Tue Mar  6 2012 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de>
- fixed urls (#800236)

* Sat Jan 14 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.2.2.35-1702
- Rebuilt for https://fedoraproject.org/wiki/Fedora_17_Mass_Rebuild

* Sat Dec 17 2011 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.2.2.35-1701
- added 'su' logrotate option (#751525)
- fixed systemd unit file; customization of TimeoutSec + LimitNOFILE is
  not possible by environment variables. Hardcode some values which can
  be overridden by the systemd .include method (#755167).
- added systemd rule in the postrotate script

* Sat Dec 17 2011 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.2.2.35-1700
- updated to 0.2.2.35 (security)
- CVE-2011-2778: Tor heap-based buffer overflow

* Fri Oct 28 2011 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.2.2.34-1700
- updated to 0.2.2.34; critical privacy/anonymity fixes
- CVE-2011-2768
- CVE-2011-2769

* Wed Oct 26 2011 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.2.2.33-1701
- Rebuilt for glibc bug#747377

* Sun Sep 18 2011 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.2.2.33-1700
- updated to 2.2.33
- removed -doc subpackage because shipped files are not available
  anymore
- ship torify files only in torify subpackage; not in main one
- start systemd service after nss-lookup.target (#719476)

* Thu Jul 28 2011 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.2.1.30-1700
- added and use systemd macros

* Thu Mar 17 2011 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.2.1.30-1601
- made EnvironmentFile in systemd definition optional
- systemd: added Requires: for core package; made it noarch

* Mon Feb 28 2011 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.2.1.30-1600
- updated to 0.2.1.30
- added 'torify' script (#669684)

* Wed Feb 09 2011 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.2.1.29-1501
- Rebuilt for https://fedoraproject.org/wiki/Fedora_15_Mass_Rebuild

* Mon Jan 17 2011 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.2.1.29-1500
- updated to 0.2.1.29 (SECURITY)
- CVE-2011-0427: heap overflow bug, potential remote code execution

* Tue Dec 21 2010 Luke Macken <lmacken@redhat.com> - 0.2.1.28-1502
- updated to 0.2.1.28 (SECURITY: fixes a remotely exploitable heap overflow bug)

* Tue Dec  7 2010 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.2.1.27-1501
- replaced lsb and sysv init stuff with systemd init script

* Fri Nov 26 2010 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.2.1.27-1500
- updated to 0.2.1.27
- added tmpfiles.d file to create %%_var/run/%%name directory in -lsb
- work around broken chkconfig by adding dummy Default-Start: in -lsb

* Fri Nov 26 2010 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.2.1.26-1500
- fixed 'limit' statement in upstart script

* Tue Jun  1 2010 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.2.1.26-1400
- updated to 0.2.1.26
- log to syslog as request by upstream (#532373#19)
- removed workaround to install lsb initscript because parts of the
  underlying problem have been fixed in redhat-lsb and the remaining
  ones were solved by previous commit
- removed $local_fs dependency in -lsb initscript to workaround
  buggy redhat-lsb; $remote_fs should imply it and has been moved to
  Should-Start:

* Tue Jun  1 2010 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de>
- created -doc subpackage and moved most (all) files from main into it

* Sun Mar 28 2010 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de>
- added -sysv subpackage

* Thu Mar 18 2010 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.2.1.25-1400
- updated to 0.2.1.25

* Wed Mar  3 2010 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.2.1.24-1402
- removed /var/lib/tor-data dir (Chen Lei)

* Tue Mar  2 2010 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.2.1.24-1401
- require tor-core, not tor in -upstart (thx to Dave Jones)

* Sat Feb 27 2010 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.2.1.24-1400
- updated to 0.2.1.24

* Mon Feb 15 2010 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.2.1.23-1300
- updated to 0.2.1.23

* Thu Jan 21 2010 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.2.1.22-1300
- updated to 0.2.1.22
