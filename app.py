#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
import logging
from flask import render_template, request, Response, flash, redirect, url_for, jsonify
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from init import *
from models import *
from config import SQLALCHEMY_DATABASE_URI
from sqlalchemy import desc
from datetime import datetime

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

# connection to postgresql database
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format="EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format="EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')

#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    all_venues_info = Venue.query.order_by(Venue.city).with_entities(Venue.city, Venue.state)\
                  .group_by(Venue.city, Venue.state).all()
                  
    all_venue = Venue.query.order_by(Venue.city).all()
    all_show = Show.query.join(Venue, Show.venue_id==Venue.id).all()
    
    data = []
    
    for venue in all_venues_info:
        data.append({"city": venue.city,
                    "state": venue.state,
                    "venues": []
                    })
            
    for venue in all_venue:
        num_upcoming_shows = 0
        
        for show in all_show:
            if show.venue_id == venue.id and show.start_time > datetime.now():
                num_upcoming_shows+=1
        
        for item in data:
            if item.get('city') == venue.city:
                item.get('venues').append({
                            "id": venue.id,
                            "name": venue.name,
                            "num_upcoming_shows": num_upcoming_shows
                        })
        
    return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
    search_word = request.form.get('search_term', '')
    
    response={
        "count": Venue.query.filter(Venue.name.ilike('%' + search_word + '%')).count(),
        "data": Venue.query.filter(Venue.name.ilike('%' + search_word +'%')).all()
    }
    
    return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    data = Venue.query.get(venue_id)
    
    all_shows = Show.query.join(Artist, Show.artist_id==Artist.id).all()
    
    data.past_shows = []
    data.upcoming_shows = []
    
    for show in all_shows:
        if show.venue_id == data.id:
            if show.start_time > datetime.now():
                data.upcoming_shows.append({"artist_id": show.artist_id,
                                            "artist_name": show.artist.name,
                                            "artist_image_link": show.artist.image_link,
                                            "start_time": format_datetime(str(show.start_time))
                                            })
            else:
                data.past_shows.append({"artist_id": show.artist_id,
                                        "artist_name": show.artist.name,
                                        "artist_image_link": show.artist.image_link,
                                        "start_time": format_datetime(str(show.start_time))
                                        })
    
    data.past_shows_count = len(data.past_shows)
    data.upcoming_shows_count = len(data.upcoming_shows)
    
    return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    form = VenueForm()
    if form.validate_on_submit():
        try:
            venue = Venue(name=form.name.data,
                          city=form.city.data,
                          state=form.state.data,
                          address=form.address.data,
                          phone=form.phone.data,
                          image_link=form.image_link.data,
                          facebook_link=form.facebook_link.data,
                          genres=form.genres.data,
                          website_link=form.website_link.data,
                          seeking_talent=form.seeking_talent.data,
                          seeking_description=form.seeking_description.data
                          )
            
            db.session.add(venue)
            db.session.commit()
            
            flash('Venue ' + request.form['name'] + ' was successfully listed!')
            
            return redirect(url_for('venues'))
        except:
            db.session.rollback()
            flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
            return render_template('forms/new_venue.html', form=form)
        finally:
            db.session.close()
    else:
        flash(form.errors)
        return render_template('forms/new_venue.html', form=form)

@app.route('/venues/<venue_id>/delete', methods=['DELETE'])
def delete_venue(venue_id):
    try:
        venue = Venue.query.get(venue_id)
        
        for item in venue.shows:
            db.session.delete(item)
        
        db.session.delete(venue)
        db.session.commit()
        
        flash('Venue ' + venue.name + ' deleted successfully.')
        return jsonify({'success': True})
    except:
        db.session.rollback()
        flash('Delete venue failed. Please try again!')
    finally:
        db.session.close()
        
#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
    data = Artist.query.all()
    return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
    search_word = request.form.get('search_term', '')
    
    response={
        "count": Artist.query.filter(Artist.name.ilike('%' + search_word + '%')).count(),
        "data": Artist.query.filter(Artist.name.ilike('%' + search_word + '%')).all()
    }
    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    data = Artist.query.get(artist_id)
    
    all_shows = Show.query.join(Venue, Show.venue_id==Venue.id).all() 
    
    data.past_shows = []
    data.upcoming_shows = []
    
    for show in all_shows:
        if show.artist_id == data.id:
            if show.start_time > datetime.now():
                data.upcoming_shows.append({
                                        "venue_id": show.venue_id,
                                        "venue_name": show.venue.name,
                                        "venue_image_link": show.venue.image_link,
                                        "start_time": format_datetime(str(show.start_time))
                                      })
            else:
                data.past_shows.append({
                                        "venue_id": show.venue_id,
                                        "venue_name": show.venue.name,
                                        "venue_image_link": show.venue.image_link,
                                        "start_time": format_datetime(str(show.start_time))
                                      })
    
    data.past_shows_count = len(data.past_shows)
    data.upcoming_shows_count = len(data.upcoming_shows)
    
    return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    artist = Artist.query.get(artist_id)
    
    artist={
      "id": artist.id,
      "name": artist.name,
      "genres": artist.genres,
      "city": artist.city,
      "state": artist.state,
      "phone": artist.phone,
      "website_link": artist.website_link,
      "facebook_link": artist.facebook_link,
      "seeking_venue": artist.seeking_venue,
      "seeking_description": artist.seeking_description,
      "image_link": artist.image_link
    }
    
    form = ArtistForm(data=artist)
    return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    form = ArtistForm()
    if form.validate_on_submit():
        try:
            artist = Artist.query.get(artist_id)
            
            artist.name = form.name.data
            artist.city = form.city.data
            artist.state = form.state.data
            artist.phone = form.phone.data
            artist.genres = form.genres.data
            artist.image_link = form.image_link.data
            artist.facebook_link = form.facebook_link.data
            artist.website_link = form.website_link.data
            artist.seeking_venue = form.seeking_venue.data
            artist.seeking_description = form.seeking_description.data
            
            db.session.commit()
            
            flash('Artist ' + request.form['name'] + ' was successfully updated!')
            return redirect(url_for('show_artist', artist_id=artist_id))
        except:
            db.session.rollback()
            flash('An error occurred. Update Artist ' + request.form['name'] + ' was failed.')
            return render_template('forms/edit_artist.html', form=form)
        finally:
                db.session.close()
    else:
        flash(form.errors)
        return redirect(url_for('edit_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    venue = Venue.query.get(venue_id)
    
    venue={
      "id": venue.id,
      "name": venue.name,
      "genres": venue.genres,
      "address": venue.address,
      "city": venue.city,
      "state": venue.state,
      "phone": venue.phone,
      "website_link": venue.website_link,
      "facebook_link": venue.facebook_link,
      "seeking_talent": venue.seeking_talent,
      "seeking_description": venue.seeking_description,
      "image_link": venue.image_link
    }
    
    form = VenueForm(data=venue)
    return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    form = VenueForm()
    if form.validate_on_submit():
        try:
            venue = Venue.query.get(venue_id)
            
            venue.name = form.name.data
            venue.city = form.city.data
            venue.state = form.state.data
            venue.address = form.address.data
            venue.phone = form.phone.data
            venue.image_link = form.image_link.data
            venue.facebook_link = form.facebook_link.data
            venue.genres = form.genres.data
            venue.website_link = form.website_link.data
            venue.seeking_talent = form.seeking_talent.data
            venue.seeking_description = form.seeking_description.data
                
            db.session.commit()
            
            flash('Venue ' + request.form['name'] + ' was successfully updated!')
            
            return redirect(url_for('show_venue', venue_id=venue_id))
        except:
            db.session.rollback()
            flash('An error occurred. Update Venue ' + request.form['name'] + ' was failed.')
            return render_template('forms/edit_venue.html', form=form)
        finally:
            db.session.rollback()
    else:
        flash(form.errors)
        return redirect(url_for('edit_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    form = ArtistForm()
    if form.validate_on_submit():
        try:
            artist = Artist(name=form.name.data,
                            city=form.city.data,
                            state=form.state.data,
                            phone=form.phone.data,
                            genres=form.genres.data,
                            image_link=form.image_link.data,
                            facebook_link=form.facebook_link.data,
                            website_link=form.website_link.data,
                            seeking_venue=form.seeking_venue.data,
                            seeking_description=form.seeking_description.data)
            
            db.session.add(artist)
            db.session.commit()
            
            flash('Artist ' + request.form['name'] + ' was successfully listed!')

            return redirect(url_for('artists'))
        except:
            db.session.rollback()
            flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
        
            return render_template('forms/new_artist.html', form=form)
        finally:
            db.session.close()
    else:
        flash(form.errors)
        return render_template('forms/new_artist.html', form=form)
        
#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    all_shows = Show.query.join(Artist, Show.artist_id==Artist.id)\
                .join(Venue, Show.venue_id==Venue.id)\
                .order_by(desc(Show.start_time))\
                .limit(10).all()
    
    data = []
    
    for show in all_shows:
        data.append({
                    "venue_id": show.venue_id,
                    "artist_id": show.artist_id,
                    "artist_name": show.artist.name,
                    "artist_image_link": show.artist.image_link,
                    "venue_name": show.venue.name,
                    "start_time": format_datetime(str(show.start_time))
                    })
        
    return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    form = ShowForm()
    if form.validate_on_submit():
        try:
            show = Show(artist_id=form.artist_id.data,
                        venue_id=form.venue_id.data,
                        start_time=form.start_time.data
                        )
            
            db.session.add(show)
            db.session.commit()
            
            flash('Show was successfully listed!')
            
            return redirect(url_for('index'))
        except:
            db.session.rollback()
            flash('An error occurred. Show could not be listed.')
            return render_template('forms/new_show.html', form=form)
        finally:
            db.session.close()
    else:
        flash(form.errors)
        return render_template('forms/new_show.html', form=form)

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
