# Deployment Guide

## Environment Setup

1. Copy `.env.example` to `.env` and configure:
```bash
cp .env.example .env
```

2. Update environment variables in `.env`:
```
DJANGO_SECRET_KEY=your-secure-secret-key
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DATABASE_URL=postgresql://user:password@localhost:5432/bookings_quality
```

## Database Setup

1. Run migrations:
```bash
python manage.py migrate
```

2. Create superuser:
```bash
python manage.py createsuperuser
```

## Production Checklist

- [ ] Set `DEBUG=False`
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Set secure `DJANGO_SECRET_KEY`
- [ ] Configure production database
- [ ] Set up static file serving
- [ ] Configure logging
- [ ] Set up SSL/HTTPS
- [ ] Configure rate limiting

## Performance Optimizations Applied

- Database indexes on frequently queried fields
- Bulk operations for file uploads
- Query optimization with select_related/prefetch_related
- API rate limiting
- Efficient JavaScript DOM manipulation
- Logging for monitoring

## Security Improvements Applied

- XSS protection with HTML escaping
- Environment-based configuration
- API throttling
- Input validation
- Secure JavaScript practices