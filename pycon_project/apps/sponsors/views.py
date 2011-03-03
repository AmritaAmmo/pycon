from functools import wraps
from itertools import groupby

from django.http import HttpResponse
from django.shortcuts import render_to_response, redirect, get_object_or_404
from django.template import RequestContext

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required

from sponsors.forms import SponsorApplicationForm, SponsorDetailsForm, SponsorBenefitsFormSet
from sponsors.models import Sponsor, SponsorBenefit


def require_no_sponsorship(only_active=False):
    def inner(func):
        @wraps(func)
        def view(request, *args, **kwargs):
            if request.user.is_authenticated():
                try:
                    sponsorship = request.user.sponsorship
                except Sponsor.DoesNotExist:
                    pass
                else:
                    if not only_active or sponsorship.active:
                        return redirect(sponsorship)
            return func(request, *args, **kwargs)
        return view
    return inner


@require_no_sponsorship(only_active=True)
def sponsor_index(request):
    return render_to_response("sponsors/index.html", {
    }, context_instance=RequestContext(request))


@login_required
@require_no_sponsorship()
def sponsor_apply(request):
    if request.method == "POST":
        form = SponsorApplicationForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            return redirect("sponsor_index")
    else:
        form = SponsorApplicationForm(user=request.user)
    return render_to_response("sponsors/apply.html", {
        "form": form,
    }, context_instance=RequestContext(request))


@login_required
def sponsor_detail(request, pk):
    sponsor = get_object_or_404(Sponsor, pk=pk)
    if not sponsor.active or sponsor.applicant != request.user:
        return redirect("sponsor_index")

    formset_kwargs = {'instance': sponsor,
                      'queryset': SponsorBenefit.objects.filter(active=True)}
    
    if request.method == "POST":
        form = SponsorDetailsForm(request.POST, instance=sponsor)
        formset = SponsorBenefitsFormSet(request.POST, request.FILES,
                                         **formset_kwargs)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            # @@@ user message here?
            return redirect(request.path)
    else:
        form = SponsorDetailsForm(instance=sponsor)
        formset = SponsorBenefitsFormSet(**formset_kwargs)
    
    return render_to_response("sponsors/detail.html", {
        "sponsor": sponsor,
        "form": form,
        "formset": formset,
    }, context_instance=RequestContext(request))


@staff_member_required
def sponsor_export_data(request):
    sponsors = []
    data = ""
    
    for sponsor in Sponsor.objects.all():
        d = {
            "name": sponsor.name,
            "url": sponsor.external_url,
            "level": (sponsor.level.order, sponsor.level.name),
            "description": "",
        }
        for sponsor_benefit in sponsor.sponsor_benefits.all():
            if sponsor_benefit.benefit_id == 2:
                d["description"] = sponsor_benefit.text
        sponsors.append(d)
    
    def level_key(s):
        return s["level"]
    
    for level, level_sponsors in groupby(sorted(sponsors, key=level_key), level_key):
        data += "%s\n" % ("-" * (len(level[1])+4))
        data += "| %s |\n" % level[1]
        data += "%s\n\n" % ("-" * (len(level[1])+4))
        for sponsor in level_sponsors:
            description = sponsor["description"].strip()
            description = description if description else "-- NO DESCRIPTION FOR THIS SPONSOR --"
            data += "%s\n\n%s" % (sponsor["name"], description)
            data += "\n\n%s\n\n" % ("-"*80)
    
    return HttpResponse(data, content_type="text/plain;charset=utf-8")
